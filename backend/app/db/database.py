"""The data access handle handed to request handlers.

The data store is a remote service, so the underlying client is process-wide
and keeps its connection alive between requests. The repositories hang off the
handle, which is what handlers receive in place of the old database session::

    db = Depends(get_db)
    key = db.api_keys.get_for_user(key_id, current_user.id)
"""

from __future__ import annotations

from collections.abc import Generator

from app.db.client import PyronitesClient, SqlClient
from app.db.repositories import (
    APIKeyRepository,
    ExternalServiceRepository,
    OAuthIdentityRepository,
    RefreshTokenRepository,
    UsageLogRepository,
    UserRepository,
    WebhookEventRepository,
    WebhookRepository,
)
from app.config import get_settings


class Database:
    """Entry point to every table the application owns."""

    def __init__(self, client: SqlClient) -> None:
        self.client = client
        self.users = UserRepository(client)
        self.api_keys = APIKeyRepository(client)
        self.external_services = ExternalServiceRepository(client)
        self.usage_logs = UsageLogRepository(client)
        self.webhooks = WebhookRepository(client)
        self.webhook_events = WebhookEventRepository(client)
        self.refresh_tokens = RefreshTokenRepository(client)
        self.oauth_identities = OAuthIdentityRepository(client)

    def ping(self) -> bool:
        """Check that the data store answers."""
        pinger = getattr(self.client, "ping", None)
        if callable(pinger):
            return bool(pinger())
        try:
            self.client.execute("SELECT 1 AS ok")
            return True
        except Exception:  # noqa: BLE001 - a health check never raises
            return False

    def close(self) -> None:
        """Release the underlying connections."""
        self.client.close()


_database: Database | None = None


def get_database() -> Database:
    """Return the process-wide database handle, creating it on first use."""
    global _database
    if _database is None:
        settings = get_settings()
        _database = Database(
            PyronitesClient(
                url=settings.pyronites_url,
                key=settings.pyronites_key,
                project_id=settings.pyronites_project_id,
                timeout=settings.pyronites_timeout,
            )
        )
    return _database


def configure_database(client: SqlClient) -> Database:
    """Replace the process-wide handle with one backed by ``client``.

    Used by the test suite and by local development against a local SQLite
    file.
    """
    global _database
    _database = Database(client)
    return _database


def reset_database() -> None:
    """Drop the process-wide handle and release its connections."""
    global _database
    if _database is not None:
        _database.close()
    _database = None


def get_db() -> Generator[Database, None, None]:
    """FastAPI dependency that yields the database handle."""
    yield get_database()
