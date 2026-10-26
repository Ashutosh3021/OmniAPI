"""Webhook delivery attempt and event payload model."""

from __future__ import annotations

import enum
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from app.models.parsing import parse_datetime


class WebhookEventStatus(str, enum.Enum):
    """Delivery status for a webhook event."""

    PENDING = "pending"
    DELIVERED = "delivered"
    FAILED = "failed"


@dataclass
class WebhookEvent:
    """Queued or completed webhook delivery with retry metadata."""

    id: int
    webhook_id: int
    user_id: int
    event_type: str
    status: str
    attempt_count: int
    created_at: datetime
    payload: str | None = None
    http_status_code: int | None = None
    error_message: str | None = None
    delivered_at: datetime | None = None
    next_retry_at: datetime | None = None

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "WebhookEvent":
        """Build a webhook event from a database row."""
        return cls(
            id=int(row["id"]),
            webhook_id=int(row["webhook_id"]),
            user_id=int(row["user_id"]),
            event_type=row["event_type"],
            status=str(row["status"]),
            attempt_count=int(row.get("attempt_count") or 0),
            created_at=parse_datetime(row["created_at"]),  # type: ignore[arg-type]
            payload=row.get("payload"),
            http_status_code=(
                int(row["http_status_code"]) if row.get("http_status_code") is not None else None
            ),
            error_message=row.get("error_message"),
            delivered_at=parse_datetime(row.get("delivered_at")),
            next_retry_at=parse_datetime(row.get("next_retry_at")),
        )

    def __repr__(self) -> str:
        return (
            f"<WebhookEvent(id={self.id}, webhook_id={self.webhook_id}, " f"status={self.status})>"
        )
