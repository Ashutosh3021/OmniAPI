"""Tests for health check endpoints."""

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


def test_liveness_returns_200_without_dependency_checks(client) -> None:
    """The load-balancer probe must never fail and never do I/O."""
    response = client.get("/api/v1/health/live")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_readiness_endpoint_exists(client) -> None:
    response = client.get("/api/v1/health/ready")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_health_unhealthy_when_db_unreachable(client_db_down) -> None:
    # Database is a critical dependency — returns 503 with "unhealthy" status
    response = client_db_down.get("/api/v1/health")
    assert response.status_code == 503
    data = response.json()
    assert data["status"] == "unhealthy"
    assert data["checks"]["database"] == "unreachable"


def test_health_unhealthy_when_redis_unreachable(client) -> None:
    # Redis is critical: the rate limiter runs on it, so without Redis every
    # authenticated request fails. The service must be pulled from rotation.
    redis_client = AsyncMock()
    redis_client.ping = AsyncMock(side_effect=ConnectionError("redis down"))
    redis_client.aclose = AsyncMock()

    with patch(
        "app.api.v1.endpoints.health.get_redis",
        return_value=redis_client,
    ):
        response = client.get("/api/v1/health")

    assert response.status_code == 503
    data = response.json()
    assert data["status"] == "unhealthy"
    assert data["checks"]["redis"] == "unreachable"


def test_health_degraded_when_celery_unreachable(client) -> None:
    # Celery only carries fire-and-forget webhook delivery; the request path
    # does not depend on it, so the service stays in rotation as "degraded".
    with patch(
        "app.api.v1.endpoints.health._check_celery",
        return_value="no_workers",
    ):
        response = client.get("/api/v1/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "degraded"
    assert data["checks"]["celery"] == "no_workers"


def test_root_endpoint(client) -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["health"] == "/api/v1/health"
