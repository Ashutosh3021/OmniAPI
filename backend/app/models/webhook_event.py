"""Webhook delivery attempt and event payload model."""

import enum
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.webhook import Webhook


class WebhookEventStatus(str, enum.Enum):
    """Delivery status for a webhook event."""

    PENDING = "pending"
    DELIVERED = "delivered"
    FAILED = "failed"


class WebhookEvent(Base):
    """Queued or completed webhook delivery with retry metadata."""

    __tablename__ = "webhook_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    webhook_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("webhooks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    payload: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[WebhookEventStatus] = mapped_column(
        Enum(
            WebhookEventStatus,
            name="webhook_event_status",
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
        server_default=WebhookEventStatus.PENDING.value,
    )
    http_status_code: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), index=True
    )
    delivered_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    next_retry_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    webhook: Mapped["Webhook"] = relationship("Webhook", back_populates="events")
    user: Mapped["User"] = relationship("User", back_populates="webhook_events")

    def __repr__(self) -> str:
        return (
            f"<WebhookEvent(id={self.id}, webhook_id={self.webhook_id}, "
            f"status={self.status})>"
        )
