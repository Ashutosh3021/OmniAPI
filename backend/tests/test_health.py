"""Tests for health check endpoint."""

from unittest.mock import AsyncMock, patch


def test_health_returns_healthy_when_all_ok(client) -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["checks"]["database"] == "ok"
    assert data["checks"]["redis"] == "ok"
    assert data["checks"]["celery"] == "ok"
    assert data["version"] == "1.0.0"


def test_health_unhealthy_when_db_unreachable(client_db_down) -> None:
    # Database is a critical dependency — returns 503 with "unhealthy" status
    response = client_db_down.get("/api/v1/health")
    assert response.status_code == 503
    data = response.json()
    assert data["status"] == "unhealthy"
    assert data["checks"]["database"] == "unreachable"


def test_health_degraded_when_redis_unreachable(client) -> None:
    # Redis is non-critical — returns 200 with "degraded" status so load
    # balancers don't take the service out of rotation when Redis is down
    redis_client = AsyncMock()
    redis_client.ping = AsyncMock(side_effect=ConnectionError("redis down"))
    redis_client.aclose = AsyncMock()

    with patch(
        "app.api.v1.endpoints.health.aioredis.from_url",
        return_value=redis_client,
    ):
        response = client.get("/api/v1/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "degraded"
    assert data["checks"]["redis"] == "unreachable"


def test_root_endpoint(client) -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["health"] == "/api/v1/health"
