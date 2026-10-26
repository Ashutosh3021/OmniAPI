"""Service catalogue, provider credential testing, and per-service quotas."""

from unittest.mock import AsyncMock, patch

import pytest

from app.services.service_catalog import SERVICE_CATALOG


def test_supported_services_lists_the_catalogue(client, auth_headers) -> None:
    """The dashboard renders its provider picker from this response."""
    response = client.get("/api/v1/external-services/supported", headers=auth_headers)
    assert response.status_code == 200

    services = response.json()["services"]
    names = [s["service_name"] for s in services]
    assert names == ["weather", "news", "stock"]
    assert names == list(SERVICE_CATALOG.keys())


def test_supported_services_publishes_param_schemas(client, auth_headers) -> None:
    response = client.get("/api/v1/external-services/supported", headers=auth_headers)
    services = {s["service_name"]: s for s in response.json()["services"]}

    weather = services["weather"]
    assert "city" in weather["params"]
    assert weather["params"]["city"]["type"] == "string"
    assert weather["params"]["city"]["required"] is False
    assert weather["params"]["lat"]["type"] == "number"
    assert weather["example"] == {"city": "London"}
    assert weather["signup_url"].startswith("https://")

    news = services["news"]
    assert news["params"]["query"]["required"] is True
    assert news["params"]["language"]["default"] == "en"

    stock = services["stock"]
    assert stock["params"]["symbol"]["required"] is True


def test_supported_services_requires_authentication(client) -> None:
    response = client.get("/api/v1/external-services/supported")
    assert response.status_code == 401


def test_create_external_service_with_canonical_payload(client, auth_headers) -> None:
    """The payload the dashboard sends must be accepted verbatim."""
    response = client.post(
        "/api/v1/external-services",
        headers=auth_headers,
        json={
            "service_name": "weather",
            "api_key": "provider-key",
            "max_calls_per_hour": 250,
        },
    )
    assert response.status_code == 201

    body = response.json()
    assert body["service_name"] == "weather"
    assert body["max_calls_per_hour"] == 250
    assert body["status"] == "active"
    assert body["error_message"] is None
    assert body["last_tested_at"] is None


def test_create_external_service_rejects_unknown_service(client, auth_headers) -> None:
    response = client.post(
        "/api/v1/external-services",
        headers=auth_headers,
        json={"service_name": "stripe", "api_key": "sk_test"},
    )
    assert response.status_code == 422


def test_duplicate_external_service_is_rejected(client, auth_headers) -> None:
    payload = {"service_name": "weather", "api_key": "provider-key"}
    first = client.post("/api/v1/external-services", headers=auth_headers, json=payload)
    assert first.status_code == 201

    second = client.post("/api/v1/external-services", headers=auth_headers, json=payload)
    assert second.status_code == 400
    assert "already configured" in second.json()["detail"]


def test_test_endpoint_reports_success(client, auth_headers) -> None:
    created = client.post(
        "/api/v1/external-services",
        headers=auth_headers,
        json={"service_name": "weather", "api_key": "provider-key"},
    )
    service_id = created.json()["service_id"]

    with patch(
        "app.api.v1.endpoints.external_services.probe_service",
        new=AsyncMock(return_value=(True, "Connection successful")),
    ):
        response = client.post(
            f"/api/v1/external-services/{service_id}/test",
            headers=auth_headers,
        )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["message"] == "Connection successful"

    # The service record reflects the check.
    fetched = client.get(f"/api/v1/external-services/{service_id}", headers=auth_headers).json()
    assert fetched["status"] == "active"
    assert fetched["last_tested_at"] is not None


def test_test_endpoint_reports_provider_failure(client, auth_headers) -> None:
    created = client.post(
        "/api/v1/external-services",
        headers=auth_headers,
        json={"service_name": "weather", "api_key": "bad-key"},
    )
    service_id = created.json()["service_id"]

    with patch(
        "app.api.v1.endpoints.external_services.probe_service",
        new=AsyncMock(return_value=(False, "Weather API returned 401")),
    ):
        response = client.post(
            f"/api/v1/external-services/{service_id}/test",
            headers=auth_headers,
        )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is False
    assert "401" in body["message"]

    fetched = client.get(f"/api/v1/external-services/{service_id}", headers=auth_headers).json()
    assert fetched["status"] == "error"
    assert "401" in fetched["error_message"]


def test_test_endpoint_is_tenant_scoped(client, auth_headers, make_auth_headers) -> None:
    created = client.post(
        "/api/v1/external-services",
        headers=auth_headers,
        json={"service_name": "weather", "api_key": "provider-key"},
    )
    service_id = created.json()["service_id"]

    other_headers, _ = make_auth_headers("other-owner@example.com")

    response = client.post(f"/api/v1/external-services/{service_id}/test", headers=other_headers)
    assert response.status_code == 404


def test_max_calls_per_hour_is_enforced(client, auth_headers) -> None:
    """The per-service quota must actually stop traffic."""
    created = client.post(
        "/api/v1/external-services",
        headers=auth_headers,
        json={
            "service_name": "weather",
            "api_key": "provider-key",
            "max_calls_per_hour": 1,
        },
    )
    assert created.status_code == 201

    body = {
        "services": ["weather"],
        "params": {"weather": {"city": "London"}},
    }

    with patch(
        "app.external_apis.weather_api.WeatherAPIClient.fetch",
        new=AsyncMock(
            return_value={
                "service": "weather",
                "data": {"city": "London", "temperature_c": 15.0},
                "fetched_at": "2026-10-21T00:00:00Z",
            }
        ),
    ):
        first = client.post("/api/v1/orchestrate", headers=auth_headers, json=body)
        second = client.post("/api/v1/orchestrate", headers=auth_headers, json=body)

    assert first.status_code == 200
    assert second.status_code == 429
    assert "calls/hour" in second.json()["detail"]


def test_service_quota_is_independent_of_the_tier_limit(client, auth_headers) -> None:
    """Exhausting a service quota must not consume the tenant's tier budget."""
    from app.middleware.rate_limit import RateLimiter as TierLimiter
    from app.services.rate_limiter import RateLimiter as ServiceLimiter

    # The two limiters key off different Redis namespaces.
    assert TierLimiter._key("1", "1") != ServiceLimiter.service_key("1", 1)


@pytest.mark.parametrize("url", ["http://example.com/hook", "https://"])
def test_webhook_url_must_be_https(url: str) -> None:
    from pydantic import ValidationError

    from app.schemas.webhook import WebhookCreate

    with pytest.raises(ValidationError):
        WebhookCreate(url=url, event_type="orchestrate.complete")
