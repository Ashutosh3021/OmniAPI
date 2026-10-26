"""Pytest fixtures for OmniAPI backend tests.

The data store is a remote HTTP service in production. The suite runs
against an in-process SQLite client that speaks the same ``SqlClient``
contract, so the real SQL — including constraints, cascades and CHECKs — is
exercised without a network round trip.
"""

import os
from collections.abc import AsyncGenerator, Generator
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from cryptography.fernet import Fernet
from dotenv import load_dotenv
from fastapi.testclient import TestClient

# Load test env before application imports (CI env vars take precedence)
_env_test = Path(__file__).resolve().parents[1] / ".env.test"
if _env_test.is_file():
    load_dotenv(_env_test, override=False)

os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("DEBUG", "True")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-pytest-only")
os.environ.setdefault("ALLOWED_ORIGINS", "http://localhost:3000")
os.environ.setdefault("REFRESH_TOKEN_EXPIRE_DAYS", "7")
os.environ.setdefault("ENCRYPTION_KEY", Fernet.generate_key().decode())
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/1")
os.environ.setdefault("CELERY_TASK_TIMEOUT", "10")
# The suite talks to the in-process SQLite client, not a remote data store.
os.environ.setdefault("PYRONITES_URL", "http://localhost:8000")
os.environ.setdefault("PYRONITES_KEY", "test-key")
os.environ.setdefault("PYRONITES_PROJECT_ID", "omniapi_test")

from app.config import get_settings  # noqa: E402
from app.db.client import DatabaseError  # noqa: E402
from app.db.database import configure_database, get_db, reset_database  # noqa: E402
from app.db.sqlite_client import SqliteClient  # noqa: E402
from app.main import create_app  # noqa: E402
from app.tasks.celery_app import celery_app  # noqa: E402

celery_app.conf.task_always_eager = True
celery_app.conf.task_store_eager_result = True
celery_app.conf.result_backend = "cache+memory://"


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers", "uses_redis: test requires real or fake Redis (no autouse mock)"
    )


@pytest.fixture(scope="session", autouse=True)
def _clear_settings_cache() -> Generator[None, None, None]:
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture(autouse=True)
def _reset_shared_clients() -> Generator[None, None, None]:
    """Reset the process-wide shared clients between tests.

    The Redis client is cached at module level, so without this a fake Redis
    created in one test would leak into the next — bound to the previous
    test's (now closed) event loop.
    """
    import app.services.redis_client as redis_client_mod

    redis_client_mod._redis = None
    _limiter_state.counts.clear()
    yield
    redis_client_mod._redis = None
    _limiter_state.counts.clear()


# Counts emulated by the fake Redis sliding-window script, so limits trip in
# tests exactly as they do in production.
_limiter_state = SimpleNamespace(counts={})


@pytest.fixture(autouse=True)
def _mock_rate_limiter(request: pytest.FixtureRequest) -> Generator[None, None, None]:
    """Allow all requests through rate limiting except dedicated rate-limiter tests."""
    if request.node.get_closest_marker("uses_redis"):
        yield
        return
    with patch("app.middleware.rate_limit.RateLimiter") as mock_cls:
        instance = mock_cls.return_value
        instance.is_allowed = AsyncMock(return_value=(True, 99))
        instance.is_allowed_service = AsyncMock(return_value=(True, 99))
        instance.is_allowed_identifier = AsyncMock(return_value=(True, 99))
        instance.get_usage = AsyncMock(return_value={"requests_in_window": 0})
        instance.retry_after_seconds = AsyncMock(return_value=60)
        instance.close = AsyncMock()
        yield


@pytest.fixture(autouse=True)
def _mock_webhook_dispatch() -> Generator[None, None, None]:
    """Prevent orchestrate tests from queueing real webhook Celery tasks."""
    with patch("app.services.orchestrator_service.WebhookService") as mock_cls:
        mock_cls.return_value.dispatch_event = MagicMock()
        yield


@pytest.fixture(autouse=True)
def _mock_redis_clients(request: pytest.FixtureRequest) -> Generator[None, None, None]:
    """Prevent tests from opening real Redis unless marked uses_redis."""
    if request.node.get_closest_marker("uses_redis"):
        yield
        return

    redis_client = AsyncMock()
    redis_client.get = AsyncMock(return_value=None)
    redis_client.set = AsyncMock()
    redis_client.delete = AsyncMock()
    redis_client.exists = AsyncMock(return_value=0)
    redis_client.zremrangebyscore = AsyncMock()
    redis_client.zcard = AsyncMock(return_value=0)
    redis_client.zadd = AsyncMock()
    redis_client.expire = AsyncMock()
    redis_client.zrange = AsyncMock(return_value=[])

    async def _fake_sliding_window(keys=None, args=None, client=None):
        """Emulate the atomic sliding-window Lua script."""
        key = keys[0]
        limit = int(args[2])
        count = _limiter_state.counts.get(key, 0)
        if count >= limit:
            return [0, 0, 60]
        _limiter_state.counts[key] = count + 1
        return [1, limit - count - 1, 0]

    redis_client.register_script = MagicMock(return_value=_fake_sliding_window)
    redis_client.pipeline = MagicMock(return_value=redis_client)
    redis_client.execute = AsyncMock(return_value=[0, 0])
    redis_client.aclose = AsyncMock()

    with (patch("app.services.redis_client.aioredis.from_url", return_value=redis_client),):
        redis_client.ping = AsyncMock(return_value=True)
        yield


@pytest.fixture(autouse=True)
def _mock_celery_inspect() -> Generator[None, None, None]:
    """Health checks report Celery as ok without a live worker."""
    with patch("app.api.v1.endpoints.health.celery_app") as mock_celery:
        # ping() returns {worker_name: {"ok": "pong"}} for each live worker
        mock_celery.control.inspect.return_value.ping.return_value = {
            "celery@test-worker": {"ok": "pong"}
        }
        yield


@pytest.fixture
def db():
    """The database handle backed by an in-process SQLite database."""
    client = SqliteClient(path=":memory:")
    database = configure_database(client)
    try:
        yield database
    finally:
        reset_database()
        client.close()


@pytest.fixture
def db_session(db):
    """Backwards-compatible alias for the database handle."""
    return db


@pytest.fixture
def app(db):
    """FastAPI application bound to the test database."""
    application = create_app()
    application.dependency_overrides[get_db] = lambda: db
    yield application
    application.dependency_overrides.clear()


@pytest.fixture
def client(app) -> Generator[TestClient, None, None]:
    """Synchronous test client."""

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def client_db_down(app, db) -> Generator[TestClient, None, None]:
    """Test client whose data store is unreachable."""

    def _boom(*args, **kwargs):
        raise DatabaseError("database down", code="unreachable")

    with patch.object(db, "ping", side_effect=_boom):
        with TestClient(app) as test_client:
            yield test_client


@pytest.fixture
async def async_client(app) -> AsyncGenerator:
    """Asynchronous test client.

    Shares the event loop with async fixtures such as ``fake_redis``, which
    a synchronous TestClient cannot do — its portal runs the app on a
    different loop.
    """
    import httpx

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def test_user(db) -> "object":
    """Pre-created active user for tests."""
    from app.models.user import UserTier

    return db.users.create(
        email="testuser@example.com",
        first_name="Test",
        last_name="User",
        tier=UserTier.FREE.value,
        created_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def access_token(db, test_user) -> str:
    """A valid access token for the test user."""
    from app.services import auth_service

    claims = auth_service.build_token_claims(test_user.id, test_user.email, test_user.tier)
    return auth_service.create_access_token(claims)


@pytest.fixture
def auth_headers(access_token) -> dict[str, str]:
    """Authorization headers with a valid JWT."""
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def make_auth_headers(db):
    """Return a factory that creates an account and returns headers for it.

    Sign-in goes through an OAuth provider, which the tests do not call. This
    factory creates the account directly and mints the same access token the
    exchange endpoint would have issued.
    """
    from datetime import datetime, timezone

    from app.services import auth_service

    def _make(email: str = "user@example.com", **user_fields):
        user = db.users.create(
            email=email,
            first_name=user_fields.pop("first_name", "Test"),
            last_name=user_fields.pop("last_name", "User"),
            tier=user_fields.pop("tier", "free"),
            created_at=datetime.now(timezone.utc),
            **user_fields,
        )
        claims = auth_service.build_token_claims(user.id, user.email, user.tier)
        token = auth_service.create_access_token(claims)
        return {"Authorization": f"Bearer {token}"}, user

    return _make


@pytest.fixture
def api_key_headers(client, auth_headers: dict[str, str]) -> dict[str, str]:
    """X-API-Key headers using a freshly created OmniAPI key."""
    create = client.post(
        "/api/v1/api-keys",
        headers=auth_headers,
        json={"name": "Test Key"},
    )
    raw_key = create.json()["raw_key"]
    return {"X-API-Key": raw_key}


@pytest.fixture
def mock_weather_response() -> dict:
    return {
        "service": "weather",
        "data": {
            "city": "London",
            "temperature_c": 15.0,
            "humidity": 60,
            "description": "cloudy",
            "wind_speed": 5.0,
        },
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }


@pytest.fixture
def mock_news_response() -> dict:
    return {
        "service": "news",
        "data": {
            "query": "AI",
            "total_results": 1,
            "articles": [
                {
                    "title": "Test",
                    "source": "Test",
                    "url": "http://example.com",
                    "published_at": "2026-01-01T00:00:00Z",
                }
            ],
        },
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }


@pytest.fixture
def mock_stock_response() -> dict:
    return {
        "service": "stock",
        "data": {
            "symbol": "AAPL",
            "price": "150.00",
            "change": "1.00",
            "change_percent": "0.67%",
            "volume": "1000000",
        },
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }


@pytest.fixture
async def fake_redis() -> AsyncGenerator:
    """Fake Redis for cache and rate-limiter unit tests."""
    import fakeredis.aioredis

    client = fakeredis.aioredis.FakeRedis(decode_responses=True)
    yield client
    await client.flushdb()
    await client.aclose()
