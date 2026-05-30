"""Pytest fixtures for OmniAPI backend tests."""

import os
from collections.abc import AsyncGenerator, Generator
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from cryptography.fernet import Fernet
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

# Load test env before application imports (CI env vars take precedence)
_env_test = Path(__file__).resolve().parents[1] / ".env.test"
if _env_test.is_file():
    load_dotenv(_env_test, override=False)

os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("DEBUG", "True")
# Fast offline suite locally; CI sets DATABASE_URL to PostgreSQL via workflow env
if os.environ.get("CI") != "true":
    os.environ["DATABASE_URL"] = "sqlite:///:memory:"
else:
    os.environ.setdefault("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/omniapi_test")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-pytest-only")
os.environ.setdefault("ALLOWED_ORIGINS", "http://localhost:3000")
os.environ.setdefault("REFRESH_TOKEN_EXPIRE_DAYS", "7")
os.environ.setdefault("ENCRYPTION_KEY", Fernet.generate_key().decode())
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/1")
os.environ.setdefault("CELERY_TASK_TIMEOUT", "10")

from app.config import get_settings  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db.session import get_db  # noqa: E402
from app.main import create_app  # noqa: E402
from app.models import APIKey, ExternalService, UsageLog, User, Webhook, WebhookEvent  # noqa: F401, E402
from app.tasks.celery_app import celery_app  # noqa: E402

celery_app.conf.task_always_eager = True
celery_app.conf.task_store_eager_result = True
celery_app.conf.result_backend = "cache+memory://"


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line("markers", "uses_redis: test requires real or fake Redis (no autouse mock)")


@pytest.fixture(scope="session", autouse=True)
def _clear_settings_cache() -> Generator[None, None, None]:
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture(autouse=True)
def _mock_rate_limiter(request: pytest.FixtureRequest) -> Generator[None, None, None]:
    """Allow all requests through rate limiting except dedicated rate-limiter tests."""
    if request.node.get_closest_marker("uses_redis"):
        yield
        return
    with patch("app.middleware.rate_limit.RateLimiter") as mock_cls:
        instance = mock_cls.return_value
        instance.is_allowed = AsyncMock(return_value=(True, 99))
        instance.get_usage = AsyncMock(return_value={"requests_in_window": 0})
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
    redis_client.pipeline = MagicMock(return_value=redis_client)
    redis_client.execute = AsyncMock(return_value=[0, 0])
    redis_client.aclose = AsyncMock()

    with (
        patch("app.services.cache_service.aioredis.from_url", return_value=redis_client),
        patch("app.services.rate_limiter.aioredis.from_url", return_value=redis_client),
        patch("app.api.v1.endpoints.health.aioredis.from_url", return_value=redis_client),
    ):
        redis_client.ping = AsyncMock(return_value=True)
        yield


@pytest.fixture(autouse=True)
def _mock_celery_inspect() -> Generator[None, None, None]:
    """Health checks report Celery as ok without a live worker."""
    with patch("app.api.v1.endpoints.health.celery_app") as mock_celery:
        mock_celery.control.inspect.return_value.active.return_value = {"worker": []}
        yield


@pytest.fixture
def db_engine():
    """In-memory SQLite engine for isolated tests."""
    from sqlalchemy import event

    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def _sqlite_fk_pragma(dbapi_connection, _connection_record) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(db_engine) -> Generator[Session, None, None]:
    """Database session with rollback after each test."""
    connection = db_engine.connect()
    transaction = connection.begin()
    session = sessionmaker(bind=connection, expire_on_commit=False)()
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def db(db_session: Session) -> Session:
    """Alias for db_session per Phase 6 spec."""
    return db_session


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """FastAPI test client with in-memory database."""

    def override_get_db() -> Generator[Session, None, None]:
        try:
            yield db_session
        finally:
            pass

    app = create_app()
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def client_db_down(db_session: Session) -> Generator[TestClient, None, None]:
    """Test client simulating database connectivity failure."""

    def override_get_db() -> Generator[Session, None, None]:
        try:
            yield db_session
        finally:
            pass

    app = create_app()
    app.dependency_overrides[get_db] = override_get_db

    with patch.object(db_session, "execute", side_effect=Exception("database down")):
        with TestClient(app) as test_client:
            yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db_session: Session) -> User:
    """Pre-created active user for tests."""
    from app.services import auth_service
    from app.models.user import User, UserTier

    user = User(
        email="testuser@example.com",
        password_hash=auth_service.hash_password("securepass123"),
        first_name="Test",
        last_name="User",
        tier=UserTier.FREE,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(client: TestClient) -> dict[str, str]:
    """Authorization headers with a valid JWT."""
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "user@example.com",
            "password": "securepass123",
            "full_name": "Test User",
        },
    )
    login = client.post(
        "/api/v1/auth/login",
        json={"email": "user@example.com", "password": "securepass123"},
    )
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def api_key_headers(client: TestClient, auth_headers: dict[str, str]) -> dict[str, str]:
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
