"""Data access for webhook subscriptions."""

from __future__ import annotations

from datetime import datetime

from app.db.client import SqlClient
from app.db.sql import sql_literal
from app.models.webhook import Webhook

TABLE = "webhooks"


class WebhookRepository:
    """Reads and writes rows in ``webhooks``."""

    def __init__(self, client: SqlClient) -> None:
        self._client = client

    def create(
        self,
        *,
        user_id: int,
        event_type: str,
        url: str,
        created_at: datetime,
        secret_encrypted: str | None = None,
    ) -> Webhook:
        """Insert a webhook subscription and return it."""
        sql = (
            f"INSERT INTO {TABLE} "
            "(user_id, event_type, url, secret_encrypted, is_active, created_at) "
            f"VALUES ({sql_literal(user_id)}, {sql_literal(event_type)}, {sql_literal(url)}, "
            f"{sql_literal(secret_encrypted)}, 1, {sql_literal(created_at)}) RETURNING *"
        )
        results = self._client.execute(sql)
        row = results[0].first() if results else None
        if row is None:
            raise RuntimeError("Webhook insert returned no row")
        return Webhook.from_row(row)

    def list_for_user(self, user_id: int) -> list[Webhook]:
        """Return every webhook of a user, newest first."""
        results = self._client.execute(
            f"SELECT * FROM {TABLE} WHERE user_id = {sql_literal(user_id)} "
            "ORDER BY created_at DESC, id DESC"
        )
        return [Webhook.from_row(row) for row in results[0].dicts()] if results else []

    def get_by_id(self, webhook_id: int) -> Webhook | None:
        """Return a webhook by id, without a tenant filter.

        Used by the delivery worker, which is handed a webhook id and not
        the owning user.
        """
        results = self._client.execute(
            f"SELECT * FROM {TABLE} WHERE id = {sql_literal(webhook_id)}"
        )
        row = results[0].first() if results else None
        return Webhook.from_row(row) if row else None

    def get_for_user(self, webhook_id: int, user_id: int) -> Webhook | None:
        """Return one of a user's webhooks, or None."""
        results = self._client.execute(
            f"SELECT * FROM {TABLE} WHERE id = {sql_literal(webhook_id)} "
            f"AND user_id = {sql_literal(user_id)}"
        )
        row = results[0].first() if results else None
        return Webhook.from_row(row) if row else None

    def list_active_for_event(self, user_id: int, event_type: str) -> list[Webhook]:
        """Return the active webhooks subscribed to an event type."""
        results = self._client.execute(
            f"SELECT * FROM {TABLE} WHERE user_id = {sql_literal(user_id)} "
            f"AND event_type = {sql_literal(event_type)} AND is_active = 1"
        )
        return [Webhook.from_row(row) for row in results[0].dicts()] if results else []

    def update(
        self,
        webhook_id: int,
        *,
        url: str | None = None,
        is_active: bool | None = None,
        updated_at: datetime,
    ) -> Webhook | None:
        """Update a webhook's URL or active state."""
        assignments = ["updated_at = " + sql_literal(updated_at)]
        if url is not None:
            assignments.append("url = " + sql_literal(url))
        if is_active is not None:
            assignments.append("is_active = " + str(1 if is_active else 0))

        sql = (
            f"UPDATE {TABLE} SET {', '.join(assignments)} "
            f"WHERE id = {sql_literal(webhook_id)} RETURNING *"
        )
        results = self._client.execute(sql)
        row = results[0].first() if results else None
        return Webhook.from_row(row) if row else None

    def record_attempt(
        self,
        webhook_id: int,
        *,
        retry_count: int,
        consecutive_failures: int,
        last_triggered_at: datetime,
        is_active: bool | None = None,
    ) -> None:
        """Record the outcome of a delivery attempt on the subscription."""
        assignments = [
            "retry_count = " + sql_literal(retry_count),
            "consecutive_failures = " + sql_literal(consecutive_failures),
            "last_triggered_at = " + sql_literal(last_triggered_at),
        ]
        if is_active is not None:
            assignments.append("is_active = " + str(1 if is_active else 0))
        self._client.execute(
            f"UPDATE {TABLE} SET {', '.join(assignments)} WHERE id = {sql_literal(webhook_id)}"
        )

    def delete(self, webhook_id: int) -> None:
        """Delete a webhook subscription."""
        self._client.execute(f"DELETE FROM {TABLE} WHERE id = {sql_literal(webhook_id)}")
