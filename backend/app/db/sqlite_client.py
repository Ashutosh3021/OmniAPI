"""A local SQLite implementation of the :class:`~app.db.client.SqlClient` contract.

The production data store is a remote HTTP service, which makes the test suite
slow and dependent on the network. This client speaks the same interface over
an in-process SQLite database, so the suite exercises the real SQL — including
constraints, cascades and CHECKs — without a network round trip.

It is also useful for local development when the Pyronites instance is not
reachable.
"""

from __future__ import annotations

import sqlite3
import threading
from pathlib import Path
from typing import Any, Iterable

from app.db.client import SqlResult
from app.db.sql import split_statements

SCHEMA_PATH = Path(__file__).with_name("schema.sql")


class SqliteClient:
    """Runs statements against a local SQLite database."""

    def __init__(
        self,
        path: str = ":memory:",
        schema: str | None = None,
        foreign_keys: bool = True,
    ) -> None:
        self._lock = threading.Lock()
        self._connection = sqlite3.connect(path, check_same_thread=False)
        self._connection.execute(
            "PRAGMA foreign_keys = ON" if foreign_keys else "PRAGMA foreign_keys = OFF"
        )
        if schema is None and path == ":memory:":
            schema = SCHEMA_PATH.read_text(encoding="utf-8")
        if schema:
            self.apply_schema(schema)

    def apply_schema(self, schema: str) -> None:
        """Apply a SQL script (the schema file) to the database."""
        with self._lock:
            for statement in split_statements(schema):
                self._connection.execute(statement)
            self._connection.commit()

    def execute(self, sql: str) -> list[SqlResult]:
        """Run the statement(s) and return one result per statement."""
        results: list[SqlResult] = []
        with self._lock:
            try:
                for statement in split_statements(sql):
                    results.append(self._run(statement))
                self._connection.commit()
            except Exception:
                self._connection.rollback()
                raise
        return results

    def _run(self, statement: str) -> SqlResult:
        cursor = self._connection.execute(statement)
        columns = [column[0] for column in cursor.description or []]
        rows: list[list[Any]] = [list(row) for row in cursor.fetchall()]
        changes = cursor.rowcount if cursor.rowcount is not None and cursor.rowcount >= 0 else 0
        cursor.close()
        return SqlResult(
            columns=columns,
            rows=rows,
            changes=changes,
            kind="select" if columns else "write",
        )

    def close(self) -> None:
        with self._lock:
            self._connection.close()

    def tables(self) -> Iterable[str]:
        """Return the names of the tables in the database."""
        with self._lock:
            rows = self._connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name"
            ).fetchall()
        return [row[0] for row in rows]
