"""Data access for webhook delivery events."""

from __future__ import annotations

from datetime import datetime

from app.db.client import SqlClient
from app.db.sql import sql_literal
from app.models.webhook_event import WebhookEvent, WebhookEventStatus

TABLE = "webhook_events"


class WebhookEventRepository:
    """Reads and writes rows in ``webhook_events``."""

    def __init__(self, client: SqlClient) -> None:
        self._client = client

    def create(
        self,
        *,
        webhook_id: int,
        user_id: int,
        event_type: str,
        payload: str | None,
        status: str = WebhookEventStatus.PENDING.value,
        attempt_count: int = 0,
        created_at: datetime,
        http_status_code: int | None = None,
        error_message: str | None = None,
        delivered_at: datetime | None = None,
    ) -> WebhookEvent:
        """Insert a delivery attempt and return it."""
        sql = (
            f"INSERT INTO {TABLE} "
            "(webhook_id, user_id, event_type, payload, status, http_status_code, "
            "error_message, attempt_count, created_at, delivered_at) "
            f"VALUES ({sql_literal(webhook_id)}, {sql_literal(user_id)}, "
            f"{sql_literal(event_type)}, {sql_literal(payload)}, {sql_literal(status)}, "
            f"{sql_literal(http_status_code)}, {sql_literal(error_message)}, "
            f"{sql_literal(attempt_count)}, {sql_literal(created_at)}, "
            f"{sql_literal(delivered_at)}) RETURNING *"
        )
        results = self._client.execute(sql)
        row = results[0].first() if results else None
        if row is None:
            raise RuntimeError("Webhook event insert returned no row")
        return WebhookEvent.from_row(row)

    def list_recent_for_webhook(self, webhook_id: int, limit: int = 10) -> list[WebhookEvent]:
        """Return the most recent delivery attempts of a webhook."""
        results = self._client.execute(
            f"SELECT * FROM {TABLE} WHERE webhook_id = {sql_literal(webhook_id)} "
            f"ORDER BY created_at DESC, id DESC LIMIT {int(limit)}"
        )
        return [WebhookEvent.from_row(row) for row in results[0].dicts()] if results else []

    def delete_older_than(self, cutoff: datetime) -> int:
        """Delete delivery attempts older than ``cutoff``."""
        results = self._client.execute(
            f"DELETE FROM {TABLE} WHERE created_at < {sql_literal(cutoff)}"
        )
        return results[0].changes if results else 0
