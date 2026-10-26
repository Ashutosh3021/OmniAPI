"""Identity of a user at an external OAuth provider."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from app.models.parsing import parse_bool, parse_datetime


@dataclass
class OAuthIdentity:
    """A Google or GitHub account linked to an OmniAPI user.

    The pair ``(provider, provider_user_id)`` is the stable key: a provider
    user id never changes, while the email address behind it can.
    """

    id: int
    user_id: int
    provider: str
    provider_user_id: str
    email: str | None
    email_verified: bool
    display_name: str | None
    avatar_url: str | None
    created_at: datetime
    updated_at: datetime | None = None

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "OAuthIdentity":
        """Build an identity from a database row."""
        return cls(
            id=int(row["id"]),
            user_id=int(row["user_id"]),
            provider=row["provider"],
            provider_user_id=row["provider_user_id"],
            email=row.get("email"),
            email_verified=parse_bool(row.get("email_verified")),
            display_name=row.get("display_name"),
            avatar_url=row.get("avatar_url"),
            created_at=parse_datetime(row["created_at"]),  # type: ignore[arg-type]
            updated_at=parse_datetime(row.get("updated_at")),
        )

    def __repr__(self) -> str:
        return (
            f"<OAuthIdentity(id={self.id}, user_id={self.user_id}, " f"provider={self.provider!r})>"
        )
