"""Data access for OAuth identities."""

from __future__ import annotations

from datetime import datetime

from app.db.client import SqlClient
from app.db.sql import sql_literal
from app.models.oauth_identity import OAuthIdentity

TABLE = "omniapi_oauth_identities"


class OAuthIdentityRepository:
    """Reads and writes rows in ``omniapi_oauth_identities``."""

    def __init__(self, client: SqlClient) -> None:
        self._client = client

    def get_by_provider(self, provider: str, provider_user_id: str) -> OAuthIdentity | None:
        """Return the identity for a provider account, or None."""
        results = self._client.execute(
            f"SELECT * FROM {TABLE} WHERE provider = {sql_literal(provider)} "
            f"AND provider_user_id = {sql_literal(provider_user_id)}"
        )
        row = results[0].first() if results else None
        return OAuthIdentity.from_row(row) if row else None

    def list_for_user(self, user_id: int) -> list[OAuthIdentity]:
        """Return every identity linked to a user."""
        results = self._client.execute(
            f"SELECT * FROM {TABLE} WHERE user_id = {sql_literal(user_id)} ORDER BY id"
        )
        return [OAuthIdentity.from_row(row) for row in results[0].dicts()] if results else []

    def create(
        self,
        *,
        user_id: int,
        provider: str,
        provider_user_id: str,
        email: str | None,
        email_verified: bool,
        display_name: str | None,
        avatar_url: str | None,
        created_at: datetime,
    ) -> OAuthIdentity:
        """Link a provider account to a user."""
        sql = (
            f"INSERT INTO {TABLE} "
            "(user_id, provider, provider_user_id, email, email_verified, "
            "display_name, avatar_url, created_at) "
            f"VALUES ({sql_literal(user_id)}, {sql_literal(provider)}, "
            f"{sql_literal(provider_user_id)}, {sql_literal(email)}, "
            f"{1 if email_verified else 0}, {sql_literal(display_name)}, "
            f"{sql_literal(avatar_url)}, {sql_literal(created_at)}) RETURNING *"
        )
        results = self._client.execute(sql)
        row = results[0].first() if results else None
        if row is None:
            raise RuntimeError("OAuth identity insert returned no row")
        return OAuthIdentity.from_row(row)

    def update(
        self,
        identity_id: int,
        *,
        email: str | None = None,
        email_verified: bool | None = None,
        display_name: str | None = None,
        avatar_url: str | None = None,
        updated_at: datetime,
    ) -> OAuthIdentity | None:
        """Refresh the cached profile details of a linked identity."""
        assignments = ["updated_at = " + sql_literal(updated_at)]
        if email is not None:
            assignments.append("email = " + sql_literal(email))
        if email_verified is not None:
            assignments.append("email_verified = " + str(1 if email_verified else 0))
        if display_name is not None:
            assignments.append("display_name = " + sql_literal(display_name))
        if avatar_url is not None:
            assignments.append("avatar_url = " + sql_literal(avatar_url))

        sql = (
            f"UPDATE {TABLE} SET {', '.join(assignments)} "
            f"WHERE id = {sql_literal(identity_id)} RETURNING *"
        )
        results = self._client.execute(sql)
        row = results[0].first() if results else None
        return OAuthIdentity.from_row(row) if row else None
