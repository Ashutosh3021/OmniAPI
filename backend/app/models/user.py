"""User account model."""

from __future__ import annotations

import enum
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from app.models.parsing import parse_bool, parse_datetime


class UserTier(str, enum.Enum):
    """Subscription tier for a user account."""

    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


@dataclass
class User:
    """An OmniAPI user.

    An account is identified by an OAuth identity (Google or GitHub). There is
    no password: the provider is the only way in.
    """

    id: int
    email: str
    first_name: str | None
    last_name: str | None
    tier: str
    is_active: bool
    created_at: datetime
    updated_at: datetime | None = None
    last_login: datetime | None = None

    @property
    def user_id(self) -> int:
        """Alias for id used in JWT claims and tenant scoping."""
        return self.id

    @property
    def full_name(self) -> str:
        """Display name from first and last name fields."""
        parts = [self.first_name, self.last_name]
        return " ".join(part for part in parts if part)

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "User":
        """Build a user from a database row."""
        return cls(
            id=int(row["id"]),
            email=row["email"],
            first_name=row.get("first_name"),
            last_name=row.get("last_name"),
            tier=str(row.get("tier") or UserTier.FREE.value),
            is_active=parse_bool(row.get("is_active")),
            created_at=parse_datetime(row["created_at"]),  # type: ignore[arg-type]
            updated_at=parse_datetime(row.get("updated_at")),
            last_login=parse_datetime(row.get("last_login")),
        )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email!r}, tier={self.tier})>"
