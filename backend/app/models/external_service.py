"""External third-party API service credentials model."""

import enum
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.usage_log import UsageLog
    from app.models.user import User


class ExternalServiceStatus(str, enum.Enum):
    """Operational status of an external service integration."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"


class ExternalService(Base):
    """User-configured external API (e.g. OpenWeatherMap, NewsAPI)."""

    __tablename__ = "external_services"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    service_name: Mapped[str] = mapped_column(String(100), nullable=False)
    api_key_encrypted: Mapped[str] = mapped_column(String(500), nullable=False)
    max_calls_per_hour: Mapped[int] = mapped_column(Integer, nullable=False, server_default="100")
    status: Mapped[ExternalServiceStatus] = mapped_column(
        Enum(
            ExternalServiceStatus,
            name="external_service_status",
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
        server_default=ExternalServiceStatus.ACTIVE.value,
    )
    error_message: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), index=True
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, onupdate=func.now()
    )
    last_tested_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    user: Mapped["User"] = relationship("User", back_populates="external_services")
    usage_logs: Mapped[List["UsageLog"]] = relationship(
        "UsageLog", back_populates="service", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return (
            f"<ExternalService(id={self.id}, user_id={self.user_id}, "
            f"service_name={self.service_name!r})>"
        )
