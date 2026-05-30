"""End-to-end happy path across auth, orchestrate, analytics, and webhooks."""

from contextlib import contextmanager
from unittest.mock import MagicMock, patch

from app.services.cache_service import CacheService


@contextmanager
def _orchestrate_mocks(weather_payload: dict, news_payload: dict):
    from unittest.mock import AsyncMock

    cache_store: dict[str, dict] = {}

    async def fake_get(key: str):
        return cache_store.get(key)

    async def fake_set(key: str, value: dict, ttl_seconds: int) -> None:
        cache_store[key] = value

    fetch_map = {
        "weather": weather_payload,
        "news": news_payload,
    }

    def fetch_side_effect(client_cls, _encrypted_key, _params):
        from app.external_apis.news_api import NewsAPIClient
        from app.external_apis.weather_api import WeatherAPIClient

        if client_cls is WeatherAPIClient:
            return fetch_map["weather"]
        if client_cls is NewsAPIClient:
            return fetch_map["news"]
        raise ValueError("unexpected client")

    with (
        patch(
            "app.tasks.external_api_tasks._run_fetch",
            side_effect=fetch_side_effect,
        ),
        patch.object(CacheService, "get", side_effect=fake_get),
        patch.object(CacheService, "set", side_effect=fake_set),
        patch.object(CacheService, "close", new_callable=AsyncMock),
        patch(
            "asyncio.to_thread",
            side_effect=lambda fn, *args, **kwargs: fn(*args, **kwargs),
        ),
        patch("app.services.orchestrator_service.WebhookService") as mock_wh,
    ):
        mock_wh.return_value.dispatch_event = MagicMock()
        yield mock_wh


def test_full_happy_path(
    client,
    mock_weather_response: dict,
    mock_news_response: dict,
) -> None:
    register = client.post(
        "/api/v1/auth/register",
        json={
            "email": "flow@example.com",
            "password": "securepass123",
            "full_name": "Flow User",
        },
    )
    assert register.status_code == 201

    login = client.post(
        "/api/v1/auth/login",
        json={"email": "flow@example.com", "password": "securepass123"},
    )
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    key_resp = client.post(
        "/api/v1/api-keys",
        headers=headers,
        json={"name": "Flow Key"},
    )
    assert key_resp.json()["raw_key"].startswith("omni_")

    for service, api_key in [("weather", "w-key"), ("news", "n-key")]:
        resp = client.post(
            "/api/v1/external-services",
            headers=headers,
            json={"service_name": service, "api_key": api_key},
        )
        assert resp.status_code == 201

    body = {
        "services": ["weather", "news"],
        "params": {
            "weather": {"city": "London"},
            "news": {"query": "AI"},
        },
    }

    with _orchestrate_mocks(mock_weather_response, mock_news_response) as mock_wh:
        first = client.post("/api/v1/orchestrate", headers=headers, json=body)
        assert first.status_code == 200
        mock_wh.return_value.dispatch_event.assert_called()

        second = client.post("/api/v1/orchestrate", headers=headers, json=body)
        assert second.status_code == 200
        hits = [r["cache_hit"] for r in second.json()["results"]]
        assert all(hits), "second orchestrate should be fully cached"

    analytics = client.get(
        "/api/v1/analytics/usage?period=last_24h",
        headers=headers,
    )
    assert analytics.status_code == 200
    metrics = analytics.json()["metrics"]
    assert metrics["total_calls"] == 4
    assert metrics["cache_hits"] == 2

    webhook = client.post(
        "/api/v1/webhooks",
        headers=headers,
        json={
            "url": "https://example.com/hooks",
            "event_type": "orchestrate.complete",
        },
    )
    assert webhook.status_code == 201
