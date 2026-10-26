"""Outbound webhook subscription model."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from app.models.parsing import parse_bool, parse_datetime


@dataclass
class Webhook:
    """User webhook endpoint for orchestration and rate-limit events."""

    id: int
    user_id: int
    event_type: str
    url: str
    is_active: bool
    retry_count: int
    max_retries: int
    consecutive_failures: int
    created_at: datetime
    secret_encrypted: str | None = None
    updated_at: datetime | None = None
    last_triggered_at: datetime | None = None

    @property
    def webhook_id(self) -> int:
        """Alias for id used in API responses."""
        return self.id

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "Webhook":
        """Build a webhook from a database row."""
        return cls(
            id=int(row["id"]),
            user_id=int(row["user_id"]),
            event_type=row["event_type"],
            url=row["url"],
            is_active=parse_bool(row.get("is_active")),
            retry_count=int(row.get("retry_count") or 0),
            max_retries=int(row.get("max_retries") or 0),
            consecutive_failures=int(row.get("consecutive_failures") or 0),
            created_at=parse_datetime(row["created_at"]),  # type: ignore[arg-type]
            secret_encrypted=row.get("secret_encrypted"),
            updated_at=parse_datetime(row.get("updated_at")),
            last_triggered_at=parse_datetime(row.get("last_triggered_at")),
        )

    def __repr__(self) -> str:
        return f"<Webhook(id={self.id}, user_id={self.user_id}, event_type={self.event_type!r})>"
