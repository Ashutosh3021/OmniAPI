"""Pytest fixtures for OmniAPI backend tests."""

import os
from collections.abc import Generator
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

# Environment must be set before application imports
os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("DEBUG", "True")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-pytest-only")
os.environ.setdefault("ALLOWED_ORIGINS", "http://localhost:3000")
os.environ.setdefault("REFRESH_TOKEN_EXPIRE_DAYS", "7")

from app.config import get_settings
from app.db.base import Base
from app.db.session import get_db
from app.main import create_app
from app.models import APIKey, ExternalService, UsageLog, User, Webhook, WebhookEvent  # noqa: F401


@pytest.fixture(scope="session", autouse=True)
def _clear_settings_cache() -> Generator[None, None, None]:
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def db_engine():
    """In-memory SQLite engine for isolated tests."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(db_engine) -> Generator[Session, None, None]:
    """Database session rolled back after each test."""
    session_factory = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=db_engine,
        expire_on_commit=False,
    )
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """FastAPI test client with in-memory database."""

    def override_get_db() -> Generator[Session, None, None]:
        try:
            yield db_session
        finally:
            pass

    with patch("app.api.v1.endpoints.health.check_database_connection", return_value=True):
        app = create_app()
        app.dependency_overrides[get_db] = override_get_db
        with TestClient(app) as test_client:
            yield test_client
        app.dependency_overrides.clear()


@pytest.fixture
def client_db_down() -> Generator[TestClient, None, None]:
    """Test client simulating database connectivity failure."""
    with patch("app.api.v1.endpoints.health.check_database_connection", return_value=False):
        app = create_app()
        with TestClient(app) as test_client:
            yield test_client


@pytest.fixture
def auth_headers(client: TestClient) -> dict[str, str]:
    """Register a user and return Authorization headers."""
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
