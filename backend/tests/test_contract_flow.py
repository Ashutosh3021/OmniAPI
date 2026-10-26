"""End-to-end contract flow.

Walks the exact sequence a dashboard user performs, in order, against the
real service catalogue, the real rate limiter and the real session
management. This is the contract the frontend codes against, so a change
that breaks the flow breaks this test.

Mirrors the manual script in fixplan.md §7.1.
"""

import pytest


@pytest.fixture
def real_redis(fake_redis, monkeypatch: pytest.MonkeyPatch) -> None:
    """Point the shared Redis client at the in-memory fake."""
    import app.services.redis_client as redis_client_mod

    monkeypatch.setattr(
        redis_client_mod.aioredis,
        "from_url",
        lambda *args, **kwargs: fake_redis,
    )


def _weather_ok():
    from unittest.mock import AsyncMock

    return AsyncMock(
        return_value={
            "service": "weather",
            "data": {
                "city": "London",
                "temperature_c": 15.0,
                "humidity": 60,
                "description": "cloudy",
                "wind_speed": 5.0,
            },
            "fetched_at": "2026-10-21T00:00:00Z",
        }
    )


@pytest.mark.uses_redis
async def test_dashboard_user_flow(async_client, real_redis, make_auth_headers) -> None:
    """sign in -> connect a provider -> generate a key -> make a call."""
    from unittest.mock import patch

    client = async_client

    # ------------------------------------------------------------------
    # 1. Sign in
    # ------------------------------------------------------------------
    # Sign-in goes through an OAuth provider, which this test does not call.
    # The session is issued the same way the exchange endpoint issues it.
    headers, user = make_auth_headers("flow@example.com")
    assert user.tier == "free"

    # ------------------------------------------------------------------
    # 3. Read the provider catalogue
    # ------------------------------------------------------------------
    supported = await client.get("/api/v1/external-services/supported", headers=headers)
    assert supported.status_code == 200
    services = supported.json()["services"]
    assert [s["service_name"] for s in services] == ["weather", "news", "stock"]
    weather = next(s for s in services if s["service_name"] == "weather")
    assert weather["params"]["city"]["type"] == "string"
    assert weather["example"] == {"city": "London"}

    # ------------------------------------------------------------------
    # 4. Connect the provider with the exact published field names
    # ------------------------------------------------------------------
    created = await client.post(
        "/api/v1/external-services",
        headers=headers,
        json={
            "service_name": "weather",
            "api_key": "provider-key",
            "max_calls_per_hour": 100,
        },
    )
    assert created.status_code == 201, created.text
    service = created.json()
    assert service["service_name"] == "weather"
    assert service["status"] == "active"
    assert service["max_calls_per_hour"] == 100
    assert "api_key" not in service

    # ------------------------------------------------------------------
    # 5. Verify the credential
    # ------------------------------------------------------------------
    with patch(
        "app.api.v1.endpoints.external_services.probe_service",
        new=_probe_ok(),
    ):
        tested = await client.post(
            f"/api/v1/external-services/{service['service_id']}/test",
            headers=headers,
        )
    assert tested.status_code == 200
    assert tested.json()["success"] is True

    # ------------------------------------------------------------------
    # 6. Generate an OmniAPI key
    # ------------------------------------------------------------------
    key_response = await client.post(
        "/api/v1/api-keys", headers=headers, json={"name": "Production"}
    )
    assert key_response.status_code == 201
    raw_key = key_response.json()["raw_key"]
    assert raw_key.startswith("omni_")

    # ------------------------------------------------------------------
    # 7. Orchestrate with the API key
    # ------------------------------------------------------------------
    with patch(
        "app.external_apis.weather_api.WeatherAPIClient.fetch",
        new=_weather_ok(),
    ):
        orchestrated = await client.post(
            "/api/v1/orchestrate",
            headers={"X-API-Key": raw_key},
            json={
                "services": ["weather"],
                "params": {"weather": {"city": "London"}},
            },
        )

    assert orchestrated.status_code == 200, orchestrated.text
    body = orchestrated.json()
    assert body["results"][0]["success"] is True
    assert body["results"][0]["data"]["city"] == "London"
    assert orchestrated.headers["X-Cache"] == "MISS"
    assert orchestrated.headers["X-RateLimit-Limit"]

    # ------------------------------------------------------------------
    # 8. The second call is served from cache
    # ------------------------------------------------------------------
    with patch(
        "app.external_apis.weather_api.WeatherAPIClient.fetch",
        new=_weather_ok(),
    ):
        cached = await client.post(
            "/api/v1/orchestrate",
            headers={"X-API-Key": raw_key},
            json={
                "services": ["weather"],
                "params": {"weather": {"city": "London"}},
            },
        )

    assert cached.status_code == 200
    assert cached.json()["results"][0]["cache_hit"] is True
    assert cached.headers["X-Cache"] == "HIT"

    # ------------------------------------------------------------------
    # 9. Analytics reflects the two calls
    # ------------------------------------------------------------------
    analytics = await client.get("/api/v1/analytics/usage?period=last_24h", headers=headers)
    assert analytics.status_code == 200
    metrics = analytics.json()["metrics"]
    assert metrics["total_calls"] == 2
    assert metrics["cache_hits"] == 1

    # ------------------------------------------------------------------
    # 10. Revoke the key — the record survives for attribution
    # ------------------------------------------------------------------
    key_id = key_response.json()["key_id"]
    revoked = await client.patch(
        f"/api/v1/api-keys/{key_id}",
        headers=headers,
        json={"is_active": False},
    )
    assert revoked.status_code == 200
    assert revoked.json()["is_active"] is False

    rejected = await client.post(
        "/api/v1/orchestrate",
        headers={"X-API-Key": raw_key},
        json={"services": ["weather"], "params": {"weather": {"city": "London"}}},
    )
    assert rejected.status_code == 401


def _probe_ok():
    from unittest.mock import AsyncMock

    return AsyncMock(return_value=(True, "Connection successful"))
