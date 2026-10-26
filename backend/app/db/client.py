"""SQL execution against the Pyronites data store.

The database is a remote HTTP service, not an embedded engine. Every statement
is a network round trip, so this client keeps a persistent (keep-alive)
connection — a fresh connection per query costs roughly five times as much —
and the repositories batch several statements into a single request whenever
they need more than one result.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any, Protocol

import httpx

logger = logging.getLogger(__name__)

# A connection that never reached the server is safe to retry: the statement
# did not run. Anything else (timeout, 5xx) is ambiguous and is surfaced.
_MAX_CONNECT_ATTEMPTS = 2

# The edge in front of the data store filters request bodies and answers 403
# when a request looks like an injection attempt. Such a block happens before
# the request reaches the data store, so retrying it is safe.
_MAX_BLOCK_RETRIES = 1
_BLOCK_RETRY_DELAY_SECONDS = 1.5


class DatabaseError(RuntimeError):
    """Raised when the data store rejects a statement or cannot be reached.

    ``code`` carries the data store's own error code when it supplied one
    (``sql_error``, ``unauthorized``, ``forbidden``, ...).
    """

    def __init__(
        self,
        message: str,
        *,
        code: str | None = None,
        status_code: int | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.status_code = status_code


@dataclass(frozen=True)
class SqlResult:
    """The outcome of a single statement."""

    columns: list[str]
    rows: list[list[Any]]
    changes: int = 0
    kind: str = "select"

    def dicts(self) -> list[dict[str, Any]]:
        """Return the rows as dictionaries keyed by column name."""
        return [dict(zip(self.columns, row)) for row in self.rows]

    def first(self) -> dict[str, Any] | None:
        """Return the first row as a dictionary, or None when there are no rows."""
        rows = self.dicts()
        return rows[0] if rows else None

    def scalar(self) -> Any:
        """Return the first column of the first row, or None when empty."""
        if not self.rows or not self.rows[0]:
            return None
        return self.rows[0][0]


class SqlClient(Protocol):
    """Minimal contract the repositories need from a data store."""

    def execute(self, sql: str) -> list[SqlResult]:
        """Run one or more statements and return one result per statement."""
        ...

    def close(self) -> None:
        """Release the underlying connections."""
        ...


class PyronitesClient:
    """Talks to a Pyronites project over its SQL execution endpoint."""

    def __init__(
        self,
        url: str,
        key: str,
        project_id: str,
        timeout: float = 30.0,
        max_connections: int = 20,
    ) -> None:
        self._project_id = project_id
        self._client = httpx.Client(
            base_url=url.rstrip("/"),
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
            },
            timeout=httpx.Timeout(timeout, connect=10.0),
            limits=httpx.Limits(
                max_connections=max_connections,
                max_keepalive_connections=max_connections,
            ),
        )

    @property
    def project_id(self) -> str:
        return self._project_id

    def execute(self, sql: str) -> list[SqlResult]:
        """Run the statement(s) and return the results in statement order."""
        path = f"/api/projects/{self._project_id}/sql/execute"
        connect_attempts = 0
        block_retries = 0

        while True:
            try:
                response = self._client.post(path, json={"sql": sql})
            except (httpx.ConnectError, httpx.ConnectTimeout) as exc:
                connect_attempts += 1
                if connect_attempts >= _MAX_CONNECT_ATTEMPTS:
                    raise DatabaseError(
                        f"Could not reach the database service: {exc}", code="unreachable"
                    ) from exc
                logger.warning(
                    "Database connection failed (attempt %s/%s): %s",
                    connect_attempts,
                    _MAX_CONNECT_ATTEMPTS,
                    exc,
                )
                continue
            except httpx.HTTPError as exc:
                raise DatabaseError(
                    f"Database request failed: {exc}", code="request_failed"
                ) from exc

            if response.status_code == 403 and block_retries < _MAX_BLOCK_RETRIES:
                block_retries += 1
                logger.warning(
                    "Database request was blocked by the edge (attempt %s/%s); retrying",
                    block_retries,
                    _MAX_BLOCK_RETRIES,
                )
                time.sleep(_BLOCK_RETRY_DELAY_SECONDS)
                continue

            if response.status_code >= 400:
                raise self._to_error(response)

            try:
                body = response.json()
            except ValueError as exc:
                raise DatabaseError(
                    "Database returned a malformed response", code="bad_response"
                ) from exc

            return [_to_result(raw) for raw in body.get("results", [])]

    def ping(self) -> bool:
        """Check that the data store answers. Used by the health endpoints."""
        try:
            self.execute("SELECT 1 AS ok")
            return True
        except DatabaseError:
            logger.exception("Database health check failed")
            return False

    def close(self) -> None:
        self._client.close()

    @staticmethod
    def _to_error(response: httpx.Response) -> DatabaseError:
        code: str | None = None
        message = f"Database request failed with status {response.status_code}"
        try:
            body = response.json()
            if isinstance(body, dict):
                code = body.get("code")
                message = body.get("message") or message
        except ValueError:
            pass
        return DatabaseError(message, code=code, status_code=response.status_code)


def _to_result(raw: dict[str, Any]) -> SqlResult:
    return SqlResult(
        columns=list(raw.get("columns") or []),
        rows=[list(row) for row in (raw.get("rows") or [])],
        changes=int(raw.get("changes") or 0),
        kind=str(raw.get("kind") or "select"),
    )
