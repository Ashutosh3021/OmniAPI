"""Analytics endpoint tests."""

from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest

from app.utils import encryption


@pytest.fixture
def analytics_user(db):
    """The account the analytics tests read from."""
    return db.users.create(
        email="analytics@example.com",
        first_name="Analytics",
        last_name="User",
        created_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def auth_headers(analytics_user):
    """Authorization headers for the analytics account."""
    from app.services import auth_service

    claims = auth_service.build_token_claims(
        analytics_user.id, analytics_user.email, analytics_user.tier
    )
    return {"Authorization": f"Bearer {auth_service.create_access_token(claims)}"}


@pytest.fixture
def seeded_usage(db, analytics_user) -> None:
    """Two usage rows for the analytics account."""
    service = db.external_services.create(
        user_id=analytics_user.id,
        service_name="weather",
        api_key_encrypted=encryption.encrypt("test-key"),
        created_at=datetime.now(timezone.utc),
    )

    now = datetime.now(timezone.utc)
    db.usage_logs.insert_many(
        [
            {
                "user_id": analytics_user.id,
                "service_id": service.id,
                "endpoint": "/orchestrate/weather",
                "response_time_ms": 100,
                "status_code": 200,
                "cache_hit": True,
                "created_at": now,
            },
            {
                "user_id": analytics_user.id,
                "service_id": service.id,
                "endpoint": "/orchestrate/weather",
                "response_time_ms": 200,
                "status_code": 500,
                "cache_hit": False,
                "created_at": now,
            },
        ]
    )


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


def test_purge_old_usage_logs_removes_expired_rows(db, analytics_user) -> None:
    """The retention job must delete history past the configured window."""
    from app.tasks.maintenance_tasks import purge_old_usage_logs

    now = datetime.now(timezone.utc)
    db.usage_logs.insert_many(
        [
            {
                "user_id": analytics_user.id,
                "endpoint": "/orchestrate/weather",
                "response_time_ms": 10,
                "status_code": 200,
                "created_at": now - timedelta(days=200),
            },
            {
                "user_id": analytics_user.id,
                "endpoint": "/orchestrate/weather",
                "response_time_ms": 10,
                "status_code": 200,
                "created_at": now - timedelta(days=1),
            },
        ]
    )

    with patch("app.tasks.maintenance_tasks.get_database") as mock_database:
        mock_database.return_value = db
        result = purge_old_usage_logs()

    assert result["deleted_usage_logs"] == 1
    remaining = db.client.execute("SELECT count(*) AS n FROM usage_logs")
    assert remaining[0].rows[0][0] == 1


def test_analytics_tenant_isolation(client, db, analytics_user, seeded_usage) -> None:
    from app.services import auth_service

    other = db.users.create(
        email="other@example.com",
        first_name="Other",
        last_name="Person",
        created_at=datetime.now(timezone.utc),
    )
    claims = auth_service.build_token_claims(other.id, other.email, other.tier)
    other_headers = {"Authorization": f"Bearer {auth_service.create_access_token(claims)}"}

    response = client.get(
        "/api/v1/analytics/usage",
        headers=other_headers,
    )
    assert response.status_code == 200
    assert response.json()["metrics"]["total_calls"] == 0
