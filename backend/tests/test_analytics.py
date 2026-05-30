"""Analytics endpoint tests."""

from datetime import datetime, timezone
from unittest.mock import patch

import pytest
from sqlalchemy.orm import Session

from app.models.external_service import ExternalService, ExternalServiceStatus
from app.models.usage_log import UsageLog
from app.models.user import User
from app.utils import encryption
from app.tasks.analytics_tasks import compute_hourly_stats


@pytest.fixture
def auth_headers(client):
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "analytics@example.com",
            "password": "securepass123",
            "full_name": "Analytics User",
        },
    )
    login = client.post(
        "/api/v1/auth/login",
        json={"email": "analytics@example.com", "password": "securepass123"},
    )
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


@pytest.fixture
def seeded_usage(db_session: Session, auth_headers, client) -> None:
    from sqlalchemy import select

    user = db_session.scalar(select(User).where(User.email == "analytics@example.com"))
    service = ExternalService(
        user_id=user.id,
        service_name="weather",
        api_key_encrypted=encryption.encrypt("test-key"),
        status=ExternalServiceStatus.ACTIVE,
    )
    db_session.add(service)
    db_session.commit()
    db_session.refresh(service)

    now = datetime.now(timezone.utc)
    db_session.add_all(
        [
            UsageLog(
                user_id=user.id,
                service_id=service.id,
                endpoint="/orchestrate/weather",
                response_time_ms=100,
                status_code=200,
                cache_hit=True,
                created_at=now,
            ),
            UsageLog(
                user_id=user.id,
                service_id=service.id,
                endpoint="/orchestrate/weather",
                response_time_ms=200,
                status_code=500,
                cache_hit=False,
                created_at=now,
            ),
        ]
    )
    db_session.commit()


def test_analytics_empty_returns_zeros(client, auth_headers) -> None:
    response = client.get(
        "/api/v1/analytics/usage?period=last_24h",
        headers=auth_headers,
    )
    assert response.status_code == 200
    metrics = response.json()["metrics"]
    assert metrics["total_calls"] == 0
    assert metrics["cache_hit_rate"] == 0.0


def test_analytics_call_count(client, auth_headers, seeded_usage) -> None:
    response = client.get(
        "/api/v1/analytics/usage?period=last_24h",
        headers=auth_headers,
    )
    assert response.json()["metrics"]["total_calls"] == 2


def test_analytics_cache_hit_rate(client, auth_headers, seeded_usage) -> None:
    response = client.get(
        "/api/v1/analytics/usage?period=last_24h",
        headers=auth_headers,
    )
    assert response.json()["metrics"]["cache_hit_rate"] == 0.5


def test_analytics_usage_metrics(client, auth_headers, seeded_usage) -> None:
    response = client.get(
        "/api/v1/analytics/usage?period=last_24h",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["metrics"]["total_calls"] == 2
    assert data["metrics"]["cache_hits"] == 1
    assert data["metrics"]["cache_hit_rate"] == 0.5
    assert len(data["by_service"]) == 1
    assert data["by_service"][0]["service_name"] == "weather"


def test_analytics_csv_report(client, auth_headers, seeded_usage) -> None:
    response = client.get(
        "/api/v1/analytics/reports",
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]
    assert "usage_report.csv" in response.headers["content-disposition"]
    body = response.text
    assert "timestamp,service,response_time_ms,cache_hit,status_code" in body
    assert "weather" in body


def test_compute_hourly_stats_noop_on_empty(db_engine) -> None:
    with patch("app.tasks.analytics_tasks.SessionLocal") as mock_session:
        from sqlalchemy.orm import sessionmaker

        session = sessionmaker(bind=db_engine)()
        mock_session.return_value = session
        result = compute_hourly_stats()
    assert result["tenants_processed"] == 0


def test_analytics_tenant_isolation(client, auth_headers, seeded_usage) -> None:
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "other@example.com",
            "password": "securepass123",
            "full_name": "Other",
        },
    )
    other_login = client.post(
        "/api/v1/auth/login",
        json={"email": "other@example.com", "password": "securepass123"},
    )
    other_headers = {"Authorization": f"Bearer {other_login.json()['access_token']}"}

    response = client.get(
        "/api/v1/analytics/usage",
        headers=other_headers,
    )
    assert response.status_code == 200
    assert response.json()["metrics"]["total_calls"] == 0
