"""Server-side record of issued refresh tokens."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from app.models.parsing import parse_datetime


@dataclass
class RefreshToken:
    """A refresh token issued to a user.

    The raw token is never stored — only its SHA-256 hash. Rotation replaces
    the row's token and marks the old row revoked; presenting a revoked token
    means it leaked, so the whole family is revoked.
    """

    id: int
    user_id: int
    token_hash: str
    family_id: str
    expires_at: datetime
    created_at: datetime
    revoked_at: datetime | None = None
    replaced_by_id: int | None = None

    @property
    def is_revoked(self) -> bool:
        """Whether this token has been revoked or replaced."""
        return self.revoked_at is not None

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "RefreshToken":
        """Build a refresh token from a database row."""
        return cls(
            id=int(row["id"]),
            user_id=int(row["user_id"]),
            token_hash=row["token_hash"],
            family_id=row["family_id"],
            expires_at=parse_datetime(row["expires_at"]),  # type: ignore[arg-type]
            created_at=parse_datetime(row["created_at"]),  # type: ignore[arg-type]
            revoked_at=parse_datetime(row.get("revoked_at")),
            replaced_by_id=(
                int(row["replaced_by_id"]) if row.get("replaced_by_id") is not None else None
            ),
        )

    def __repr__(self) -> str:
        return f"<RefreshToken(id={self.id}, user_id={self.user_id})>"
