"""Data access for API keys."""

from __future__ import annotations

from datetime import datetime, timedelta

from app.db.client import SqlClient
from app.db.sql import sql_literal
from app.models.api_key import APIKey
from app.models.user import User

TABLE = "omniapi_api_keys"

# How stale ``last_used_at`` is allowed to get before it is written again.
# Writing it on every request put a write transaction on the hot path.
LAST_USED_WRITE_INTERVAL_SECONDS = 60


class APIKeyRepository:
    """Reads and writes rows in ``omniapi_api_keys``."""

    def __init__(self, client: SqlClient) -> None:
        self._client = client

    def create(
        self,
        *,
        user_id: int,
        key_hash: str,
        name: str,
        created_at: datetime,
        expires_at: datetime | None = None,
    ) -> APIKey:
        """Insert a new API key and return it."""
        sql = (
            f"INSERT INTO {TABLE} "
            "(user_id, key_hash, name, is_active, expires_at, created_at) "
            f"VALUES ({sql_literal(user_id)}, {sql_literal(key_hash)}, {sql_literal(name)}, "
            f"1, {sql_literal(expires_at)}, {sql_literal(created_at)}) RETURNING *"
        )
        results = self._client.execute(sql)
        row = results[0].first() if results else None
        if row is None:
            raise RuntimeError("API key insert returned no row")
        return APIKey.from_row(row)

    def list_for_user(self, user_id: int) -> list[APIKey]:
        """Return every key belonging to a user, newest first."""
        results = self._client.execute(
            f"SELECT * FROM {TABLE} WHERE user_id = {sql_literal(user_id)} "
            "ORDER BY created_at DESC, id DESC"
        )
        return [APIKey.from_row(row) for row in results[0].dicts()] if results else []

    def get_for_user(self, key_id: int, user_id: int) -> APIKey | None:
        """Return one of a user's keys, or None."""
        results = self._client.execute(
            f"SELECT * FROM {TABLE} WHERE id = {sql_literal(key_id)} "
            f"AND user_id = {sql_literal(user_id)}"
        )
        row = results[0].first() if results else None
        return APIKey.from_row(row) if row else None

    def find_active_by_hash(self, key_hash: str) -> tuple[APIKey, User] | None:
        """Return the active key with this hash together with its owner.

        The owner is joined in the same statement so that authenticating a
        request costs a single round trip.
        """
        sql = (
            f"SELECT k.*, u.email AS owner_email, u.tier AS owner_tier, "
            f"u.is_active AS owner_is_active, u.first_name AS owner_first_name, "
            f"u.last_name AS owner_last_name, u.created_at AS owner_created_at, "
            f"u.updated_at AS owner_updated_at, u.last_login AS owner_last_login "
            f"FROM {TABLE} AS k "
            f"JOIN omniapi_users AS u ON u.id = k.user_id "
            f"WHERE k.key_hash = {sql_literal(key_hash)} AND k.is_active = 1"
        )
        results = self._client.execute(sql)
        row = results[0].first() if results else None
        if row is None:
            return None
        return APIKey.from_row(row), User.from_row(
            {
                "id": row["user_id"],
                "email": row["owner_email"],
                "first_name": row.get("owner_first_name"),
                "last_name": row.get("owner_last_name"),
                "tier": row.get("owner_tier"),
                "is_active": row.get("owner_is_active"),
                "created_at": row.get("owner_created_at"),
                "updated_at": row.get("owner_updated_at"),
                "last_login": row.get("owner_last_login"),
            }
        )

    def update(
        self,
        key_id: int,
        *,
        name: str | None = None,
        expires_at: datetime | None = None,
        is_active: bool | None = None,
        updated_at: datetime,
    ) -> APIKey | None:
        """Update a key's name, expiry or active state."""
        assignments = ["updated_at = " + sql_literal(updated_at)]
        if name is not None:
            assignments.append("name = " + sql_literal(name))
        if expires_at is not None:
            assignments.append("expires_at = " + sql_literal(expires_at))
        if is_active is not None:
            assignments.append("is_active = " + str(1 if is_active else 0))

        sql = (
            f"UPDATE {TABLE} SET {', '.join(assignments)} "
            f"WHERE id = {sql_literal(key_id)} RETURNING *"
        )
        results = self._client.execute(sql)
        row = results[0].first() if results else None
        return APIKey.from_row(row) if row else None

    def delete(self, key_id: int) -> None:
        """Delete a key permanently."""
        self._client.execute(f"DELETE FROM {TABLE} WHERE id = {sql_literal(key_id)}")

    def touch_last_used(self, key_id: int, at: datetime) -> None:
        """Record key usage without putting a write on every request.

        A single conditional UPDATE: no read, no row lock, and concurrent
        requests cannot pile up writes for the same key.
        """
        threshold = at - timedelta(seconds=LAST_USED_WRITE_INTERVAL_SECONDS)
        self._client.execute(
            f"UPDATE {TABLE} SET last_used_at = {sql_literal(at)} "
            f"WHERE id = {sql_literal(key_id)} "
            f"AND (last_used_at IS NULL OR last_used_at < {sql_literal(threshold)})"
        )
