"""Data access for user accounts."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from app.db.client import SqlClient
from app.db.sql import sql_literal
from app.models.user import User, UserTier

TABLE = "omniapi_users"


class UserRepository:
    """Reads and writes rows in ``omniapi_users``."""

    def __init__(self, client: SqlClient) -> None:
        self._client = client

    def get_by_id(self, user_id: int) -> User | None:
        """Return the user with this id, or None."""
        results = self._client.execute(f"SELECT * FROM {TABLE} WHERE id = {sql_literal(user_id)}")
        row = results[0].first() if results else None
        return User.from_row(row) if row else None

    def get_by_email(self, email: str) -> User | None:
        """Return the user with this email address, or None."""
        results = self._client.execute(f"SELECT * FROM {TABLE} WHERE email = {sql_literal(email)}")
        row = results[0].first() if results else None
        return User.from_row(row) if row else None

    def create(
        self,
        *,
        email: str,
        first_name: str | None,
        last_name: str | None,
        tier: str = UserTier.FREE.value,
        created_at: datetime,
    ) -> User:
        """Insert a new user and return it."""
        sql = (
            f"INSERT INTO {TABLE} "
            "(email, first_name, last_name, tier, is_active, created_at) "
            f"VALUES ({sql_literal(email)}, {sql_literal(first_name)}, "
            f"{sql_literal(last_name)}, {sql_literal(tier)}, 1, "
            f"{sql_literal(created_at)}) "
            "RETURNING *"
        )
        results = self._client.execute(sql)
        row = results[0].first() if results else None
        if row is None:
            raise RuntimeError("User insert returned no row")
        return User.from_row(row)

    def update_profile(
        self,
        user_id: int,
        *,
        first_name: str | None,
        last_name: str | None,
        updated_at: datetime,
    ) -> User | None:
        """Update the display name of a user and return the new row."""
        sql = (
            f"UPDATE {TABLE} SET first_name = {sql_literal(first_name)}, "
            f"last_name = {sql_literal(last_name)}, updated_at = {sql_literal(updated_at)} "
            f"WHERE id = {sql_literal(user_id)} RETURNING *"
        )
        results = self._client.execute(sql)
        row = results[0].first() if results else None
        return User.from_row(row) if row else None

    def touch_last_login(self, user_id: int, at: datetime) -> None:
        """Record the time of the most recent sign-in."""
        self._client.execute(
            f"UPDATE {TABLE} SET last_login = {sql_literal(at)}, "
            f"updated_at = {sql_literal(at)} WHERE id = {sql_literal(user_id)}"
        )

    def set_tier(self, user_id: int, tier: str, updated_at: datetime) -> None:
        """Change a user's subscription tier."""
        self._client.execute(
            f"UPDATE {TABLE} SET tier = {sql_literal(tier)}, "
            f"updated_at = {sql_literal(updated_at)} WHERE id = {sql_literal(user_id)}"
        )

    def set_active(self, user_id: int, is_active: bool, updated_at: datetime) -> None:
        """Activate or deactivate a user account."""
        self._client.execute(
            f"UPDATE {TABLE} SET is_active = {1 if is_active else 0}, "
            f"updated_at = {sql_literal(updated_at)} WHERE id = {sql_literal(user_id)}"
        )

    def to_dict(self, user: User) -> dict[str, Any]:
        """Return the row representation of a user (used by the cache layer)."""
        return {
            "id": user.id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "tier": user.tier,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat(),
            "updated_at": user.updated_at.isoformat() if user.updated_at else None,
            "last_login": user.last_login.isoformat() if user.last_login else None,
        }
