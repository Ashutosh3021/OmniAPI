"""User account model."""

import enum
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, DateTime, Enum, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.api_key import APIKey
    from app.models.external_service import ExternalService
    from app.models.usage_log import UsageLog
    from app.models.webhook import Webhook
    from app.models.webhook_event import WebhookEvent


class UserTier(str, enum.Enum):
    """Subscription tier for a user account."""

    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class User(Base):
    """Registered OmniAPI user with tier and authentication metadata."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    first_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    tier: Mapped[UserTier] = mapped_column(
        Enum(UserTier, name="user_tier", values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        server_default=UserTier.FREE.value,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        onupdate=func.now(),
    )
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    api_keys: Mapped[List["APIKey"]] = relationship(
        "APIKey", back_populates="user", cascade="all, delete-orphan"
    )
    external_services: Mapped[List["ExternalService"]] = relationship(
        "ExternalService", back_populates="user", cascade="all, delete-orphan"
    )
    usage_logs: Mapped[List["UsageLog"]] = relationship(
        "UsageLog", back_populates="user", cascade="all, delete-orphan"
    )
    webhooks: Mapped[List["Webhook"]] = relationship(
        "Webhook", back_populates="user", cascade="all, delete-orphan"
    )
    webhook_events: Mapped[List["WebhookEvent"]] = relationship(
        "WebhookEvent", back_populates="user", cascade="all, delete-orphan"
    )

    @property
    def user_id(self) -> int:
        """Alias for id used in JWT claims and tenant scoping."""
        return self.id

    @property
    def full_name(self) -> str:
        """Display name from first and last name fields."""
        parts = [self.first_name, self.last_name]
        return " ".join(part for part in parts if part)

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email!r}, tier={self.tier})>"
