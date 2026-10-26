"""Data access for refresh tokens."""

from __future__ import annotations

from datetime import datetime

from app.db.client import SqlClient
from app.db.sql import sql_literal
from app.models.refresh_token import RefreshToken

TABLE = "refresh_tokens"


class RefreshTokenRepository:
    """Reads and writes rows in ``refresh_tokens``."""

    def __init__(self, client: SqlClient) -> None:
        self._client = client

    def create(
        self,
        *,
        user_id: int,
        token_hash: str,
        family_id: str,
        expires_at: datetime,
        created_at: datetime,
    ) -> RefreshToken:
        """Insert a refresh token and return it."""
        sql = (
            f"INSERT INTO {TABLE} "
            "(user_id, token_hash, family_id, expires_at, created_at) "
            f"VALUES ({sql_literal(user_id)}, {sql_literal(token_hash)}, "
            f"{sql_literal(family_id)}, {sql_literal(expires_at)}, "
            f"{sql_literal(created_at)}) RETURNING *"
        )
        results = self._client.execute(sql)
        row = results[0].first() if results else None
        if row is None:
            raise RuntimeError("Refresh token insert returned no row")
        return RefreshToken.from_row(row)

    def get_by_hash(self, token_hash: str) -> RefreshToken | None:
        """Return the token with this hash, revoked or not."""
        results = self._client.execute(
            f"SELECT * FROM {TABLE} WHERE token_hash = {sql_literal(token_hash)}"
        )
        row = results[0].first() if results else None
        return RefreshToken.from_row(row) if row else None

    def list_for_user(self, user_id: int) -> list[RefreshToken]:
        """Return every token issued to a user, revoked or not."""
        results = self._client.execute(
            f"SELECT * FROM {TABLE} WHERE user_id = {sql_literal(user_id)} ORDER BY id"
        )
        return [RefreshToken.from_row(row) for row in results[0].dicts()] if results else []

    def revoke(self, token_id: int, revoked_at: datetime) -> None:
        """Mark a single token as revoked."""
        self._client.execute(
            f"UPDATE {TABLE} SET revoked_at = {sql_literal(revoked_at)} WHERE id = {sql_literal(token_id)}"
        )

    def replace(self, token_id: int, replaced_by_id: int, revoked_at: datetime) -> None:
        """Mark a token as replaced by its successor."""
        self._client.execute(
            f"UPDATE {TABLE} SET revoked_at = {sql_literal(revoked_at)}, "
            f"replaced_by_id = {sql_literal(replaced_by_id)} WHERE id = {sql_literal(token_id)}"
        )

    def revoke_family(self, family_id: str, revoked_at: datetime) -> int:
        """Revoke every live token in a rotation family."""
        results = self._client.execute(
            f"UPDATE {TABLE} SET revoked_at = {sql_literal(revoked_at)} "
            f"WHERE family_id = {sql_literal(family_id)} AND revoked_at IS NULL"
        )
        return results[0].changes if results else 0

    def revoke_all_for_user(self, user_id: int, revoked_at: datetime) -> int:
        """Revoke every live token belonging to a user."""
        results = self._client.execute(
            f"UPDATE {TABLE} SET revoked_at = {sql_literal(revoked_at)} "
            f"WHERE user_id = {sql_literal(user_id)} AND revoked_at IS NULL"
        )
        return results[0].changes if results else 0

    def delete_older_than(self, cutoff: datetime) -> int:
        """Delete tokens that expired before ``cutoff``."""
        results = self._client.execute(
            f"DELETE FROM {TABLE} WHERE expires_at < {sql_literal(cutoff)}"
        )
        return results[0].changes if results else 0
