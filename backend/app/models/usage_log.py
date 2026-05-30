"""API usage log for analytics and billing."""

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.external_service import ExternalService
    from app.models.user import User


class UsageLog(Base):
    """Record of a single orchestrated API call."""

    __tablename__ = "usage_logs"
    __table_args__ = (Index("ix_usage_logs_user_id_created_at", "user_id", "created_at"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    service_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("external_services.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    endpoint: Mapped[str] = mapped_column(String(255), nullable=False)
    response_time_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    status_code: Mapped[int] = mapped_column(Integer, nullable=False, server_default="200")
    cache_hit: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    request_size_bytes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    response_size_bytes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), index=True
    )
    error_message: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="usage_logs")
    service: Mapped[Optional["ExternalService"]] = relationship(
        "ExternalService", back_populates="usage_logs"
    )

    def __repr__(self) -> str:
        return (
            f"<UsageLog(id={self.id}, user_id={self.user_id}, "
            f"endpoint={self.endpoint!r}, status_code={self.status_code})>"
        )
