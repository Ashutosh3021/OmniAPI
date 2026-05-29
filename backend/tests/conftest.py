"""Pytest fixtures for OmniAPI backend tests."""

import os
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

# Set test environment before importing app modules
os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("DEBUG", "True")
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql://postgres:password@db.testproject.supabase.co:5432/postgres",
)
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-pytest-only")
os.environ.setdefault("ALLOWED_ORIGINS", "http://localhost:3000")

from app.config import get_settings
from app.main import create_app


@pytest.fixture(scope="session", autouse=True)
def _clear_settings_cache() -> None:
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def client() -> TestClient:
    """FastAPI test client with database check mocked as connected."""
    with patch("app.api.v1.endpoints.health.check_database_connection", return_value=True):
        app = create_app()
        with TestClient(app) as test_client:
            yield test_client


@pytest.fixture
def client_db_down() -> TestClient:
    """Test client simulating database connectivity failure."""
    with patch("app.api.v1.endpoints.health.check_database_connection", return_value=False):
        app = create_app()
        with TestClient(app) as test_client:
            yield test_client
