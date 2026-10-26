"""API key model for authenticating OmniAPI requests."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from app.models.parsing import parse_bool, parse_datetime


@dataclass
class APIKey:
    """Hashed API key belonging to a user."""

    id: int
    user_id: int
    key_hash: str
    name: str
    is_active: bool
    created_at: datetime
    last_used_at: datetime | None = None
    expires_at: datetime | None = None
    updated_at: datetime | None = None

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "APIKey":
        """Build an API key from a database row."""
        return cls(
            id=int(row["id"]),
            user_id=int(row["user_id"]),
            key_hash=row["key_hash"],
            name=row["name"],
            is_active=parse_bool(row.get("is_active")),
            created_at=parse_datetime(row["created_at"]),  # type: ignore[arg-type]
            last_used_at=parse_datetime(row.get("last_used_at")),
            expires_at=parse_datetime(row.get("expires_at")),
            updated_at=parse_datetime(row.get("updated_at")),
        )

    def __repr__(self) -> str:
        return f"<APIKey(id={self.id}, user_id={self.user_id}, name={self.name!r})>"
