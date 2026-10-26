"""Data access for usage logs."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Iterable

from app.db.client import SqlClient
from app.db.sql import sql_literal
from app.models.usage_log import UsageLog

TABLE = "usage_logs"

# Columns that are NOT NULL in the schema but are often left out by the
# caller. The schema default only applies when the column is absent from the
# INSERT, so the value is filled in here instead.
_COLUMN_DEFAULTS: dict[str, Any] = {
    "status_code": 200,
    "cache_hit": False,
}


@dataclass
class UsageMetrics:
    """Aggregate counters for a set of usage rows."""

    total: int = 0
    successful: int = 0
    failed: int = 0
    cache_hits: int = 0
    avg_response_time_ms: float = 0.0
    calls_today: int = 0
    calls_yesterday: int = 0
    avg_response_time_ms_today: float = 0.0
    avg_response_time_ms_yesterday: float = 0.0

    @property
    def cache_hit_rate(self) -> float:
        """Share of calls served from the cache."""
        return (self.cache_hits / self.total) if self.total else 0.0


def _column_value(row: dict[str, Any], column: str) -> Any:
    """Return the value for a column, applying the schema default if absent."""
    value = row.get(column)
    if value is None and column in _COLUMN_DEFAULTS:
        return _COLUMN_DEFAULTS[column]
    return value


class UsageLogRepository:
    """Reads and writes rows in ``usage_logs``."""

    def __init__(self, client: SqlClient) -> None:
        self._client = client

    def insert_many(self, rows: Iterable[dict[str, Any]]) -> int:
        """Insert several usage rows in a single statement.

        One statement instead of one per row: a single orchestration call can
        produce several rows, and every extra statement is another round trip
        to the data store.
        """
        values = [row for row in rows]
        if not values:
            return 0

        columns = (
            "user_id, service_id, api_key_id, endpoint, response_time_ms, "
            "status_code, cache_hit, request_size_bytes, response_size_bytes, "
            "created_at, error_message"
        )
        tuples = ", ".join(
            "("
            + ", ".join(
                sql_literal(_column_value(row, column))
                for column in (
                    "user_id",
                    "service_id",
                    "api_key_id",
                    "endpoint",
                    "response_time_ms",
                    "status_code",
                    "cache_hit",
                    "request_size_bytes",
                    "response_size_bytes",
                    "created_at",
                    "error_message",
                )
            )
            + ")"
            for row in values
        )
        results = self._client.execute(f"INSERT INTO {TABLE} ({columns}) VALUES {tuples}")
        return results[0].changes if results else 0

    def list_for_user(
        self,
        user_id: int,
        since: datetime | None = None,
        limit: int | None = None,
    ) -> list[UsageLog]:
        """Return a user's usage rows, newest first.

        ``since`` restricts the window; ``limit`` caps the number of rows
        returned.
        """
        sql = f"SELECT * FROM {TABLE} WHERE user_id = {sql_literal(user_id)}"
        if since is not None:
            sql += f" AND created_at >= {sql_literal(since)}"
        sql += " ORDER BY created_at DESC, id DESC"
        if limit is not None:
            sql += f" LIMIT {int(limit)}"
        results = self._client.execute(sql)
        return [UsageLog.from_row(row) for row in results[0].dicts()] if results else []

    def metrics_for(
        self, user_id: int, since: datetime, today_start: datetime, yesterday_start: datetime
    ) -> UsageMetrics:
        """Compute the dashboard counters for one user in a single statement.

        The today/yesterday comparison is folded into the same statement with
        conditional aggregates, so the summary needs one round trip instead of
        two.
        """
        sql = (
            f"SELECT COUNT(*) AS total, "
            f"SUM(CASE WHEN status_code < 400 THEN 1 ELSE 0 END) AS successful, "
            f"SUM(CASE WHEN status_code >= 400 THEN 1 ELSE 0 END) AS failed, "
            f"SUM(CASE WHEN cache_hit = 1 THEN 1 ELSE 0 END) AS cache_hits, "
            f"AVG(response_time_ms) AS avg_ms, "
            f"SUM(CASE WHEN created_at >= {sql_literal(today_start)} THEN 1 ELSE 0 END) AS calls_today, "
            f"SUM(CASE WHEN created_at < {sql_literal(yesterday_start)} THEN 1 ELSE 0 END) AS calls_yesterday, "
            f"AVG(CASE WHEN created_at >= {sql_literal(today_start)} THEN response_time_ms END) AS avg_ms_today, "
            f"AVG(CASE WHEN created_at < {sql_literal(yesterday_start)} THEN response_time_ms END) AS avg_ms_yesterday "
            f"FROM {TABLE} "
            f"WHERE user_id = {sql_literal(user_id)} "
            f"AND created_at >= {sql_literal(since)}"
        )
        results = self._client.execute(sql)
        row = results[0].first() if results else None
        if row is None:
            return UsageMetrics()
        return UsageMetrics(
            total=int(row.get("total") or 0),
            successful=int(row.get("successful") or 0),
            failed=int(row.get("failed") or 0),
            cache_hits=int(row.get("cache_hits") or 0),
            avg_response_time_ms=float(row.get("avg_ms") or 0.0),
            calls_today=int(row.get("calls_today") or 0),
            calls_yesterday=int(row.get("calls_yesterday") or 0),
            avg_response_time_ms_today=float(row.get("avg_ms_today") or 0.0),
            avg_response_time_ms_yesterday=float(row.get("avg_ms_yesterday") or 0.0),
        )

    def breakdown_by_service(self, user_id: int, since: datetime) -> list[dict[str, Any]]:
        """Return per-service call counts for one user."""
        sql = (
            f"SELECT s.service_name AS service_name, "
            f"COUNT(l.id) AS call_count, "
            f"SUM(CASE WHEN l.cache_hit = 1 THEN 1 ELSE 0 END) AS cache_hits, "
            f"AVG(l.response_time_ms) AS avg_ms, "
            f"SUM(CASE WHEN l.status_code >= 400 THEN 1 ELSE 0 END) AS error_count "
            f"FROM {TABLE} AS l "
            f"JOIN external_services AS s ON s.id = l.service_id "
            f"WHERE l.user_id = {sql_literal(user_id)} "
            f"AND l.created_at >= {sql_literal(since)} "
            f"GROUP BY s.service_name "
            f"ORDER BY COUNT(l.id) DESC"
        )
        results = self._client.execute(sql)
        return results[0].dicts() if results else []

    def iter_rows_with_service(
        self, user_id: int, since: datetime, batch_size: int = 500
    ) -> Iterable[dict[str, Any]]:
        """Yield usage rows joined with their service name, in chunks.

        The join is an outer join so a call whose service was deleted still
        appears in the export.
        """
        offset = 0
        while True:
            sql = (
                f"SELECT l.created_at AS created_at, s.service_name AS service_name, "
                f"l.response_time_ms AS response_time_ms, l.cache_hit AS cache_hit, "
                f"l.status_code AS status_code "
                f"FROM {TABLE} AS l "
                f"LEFT JOIN external_services AS s ON s.id = l.service_id "
                f"WHERE l.user_id = {sql_literal(user_id)} "
                f"AND l.created_at >= {sql_literal(since)} "
                f"ORDER BY l.created_at DESC, l.id DESC "
                f"LIMIT {batch_size} OFFSET {offset}"
            )
            results = self._client.execute(sql)
            rows = results[0].dicts() if results else []
            if not rows:
                return
            yield from rows
            if len(rows) < batch_size:
                return
            offset += batch_size

    def delete_older_than(self, cutoff: datetime) -> int:
        """Delete usage rows older than ``cutoff`` and return how many went."""
        results = self._client.execute(
            f"DELETE FROM {TABLE} WHERE created_at < {sql_literal(cutoff)}"
        )
        return results[0].changes if results else 0
