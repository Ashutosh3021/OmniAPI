"""Orchestration endpoint tests (Phase 3 + Phase 4)."""

import inspect
from contextlib import contextmanager
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import select

from app.models.usage_log import UsageLog
from app.services.cache_service import CacheService


def _weather_payload() -> dict:
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


def _news_payload() -> dict:
    return {
        "service": "news",
        "data": {
            "query": "AI",
            "total_results": 1,
            "articles": [
                {"title": "Test", "source": "Test", "url": "http://x", "published_at": "t"}
            ],
        },
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }


@contextmanager
def _orchestrate_mocks(fetch_map=None, fetch_side_effect=None, cache_get_side_effect=None):
    """Patch the provider clients so no real upstream call is made.

    The orchestrator now calls the providers directly (no broker round trip),
    so the client classes are the seam to patch. ``fetch_map`` maps a service
    name to the payload that service should return; ``fetch_side_effect`` is a
    callable ``(client, params)`` for tests that need per-call behaviour.
    """
    from app.external_apis.news_api import NewsAPIClient
    from app.external_apis.stock_api import StockAPIClient
    from app.external_apis.weather_api import WeatherAPIClient

    get_kwargs: dict = {}
    if cache_get_side_effect is not None:
        get_kwargs["side_effect"] = cache_get_side_effect
    else:
        get_kwargs["return_value"] = None

    async def _fake_fetch(self, params):
        if fetch_side_effect is not None:
            outcome = fetch_side_effect(self, params)
            if inspect.isawaitable(outcome):
                outcome = await outcome
            return outcome
        if fetch_map is not None:
            return fetch_map[self.service_name]
        raise AssertionError(f"unexpected provider call to {self.service_name}")

    with (
        patch.object(WeatherAPIClient, "fetch", new=_fake_fetch),
        patch.object(NewsAPIClient, "fetch", new=_fake_fetch),
        patch.object(StockAPIClient, "fetch", new=_fake_fetch),
        patch.object(CacheService, "get", new_callable=AsyncMock, **get_kwargs),
        patch.object(CacheService, "set", new_callable=AsyncMock),
    ):
        yield


@pytest.fixture
def configured_weather(client, auth_headers) -> None:
    client.post(
        "/api/v1/external-services",
        headers=auth_headers,
        json={"service_name": "weather", "api_key": "weather-key"},
    )


@pytest.fixture
def configured_weather_and_news(client, auth_headers) -> None:
    client.post(
        "/api/v1/external-services",
        headers=auth_headers,
        json={"service_name": "weather", "api_key": "weather-key"},
    )
    client.post(
        "/api/v1/external-services",
        headers=auth_headers,
        json={"service_name": "news", "api_key": "news-key"},
    )


def test_orchestrate_weather_success(
    client, auth_headers, configured_weather, db_session
) -> None:
    with _orchestrate_mocks(fetch_map={"weather": _weather_payload()}):
        response = client.post(
            "/api/v1/orchestrate",
            headers=auth_headers,
            json={
                "services": ["weather"],
                "params": {"weather": {"city": "London"}},
            },
        )

    assert response.status_code == 200
    data = response.json()
    assert data["results"][0]["success"] is True
    assert data["results"][0]["cache_hit"] is False
    assert response.headers["X-RateLimit-Limit"]
    assert response.headers["X-RateLimit-Remaining"]
    assert response.headers["X-Cache"] == "MISS"

    logs = db_session.scalars(select(UsageLog)).all()
    assert len(logs) == 1
    assert logs[0].cache_hit is False


def test_orchestrate_cache_hit_on_second_request(
    client, auth_headers, configured_weather, db_session
) -> None:
    with _orchestrate_mocks(
        fetch_map={"weather": _weather_payload()},
        cache_get_side_effect=[None, _weather_payload()],
    ):
        body = {
            "services": ["weather"],
            "params": {"weather": {"city": "London"}},
        }
        first = client.post("/api/v1/orchestrate", headers=auth_headers, json=body)
        second = client.post("/api/v1/orchestrate", headers=auth_headers, json=body)

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["results"][0]["cache_hit"] is False
    assert second.json()["results"][0]["cache_hit"] is True

    logs = db_session.scalars(select(UsageLog)).all()
    assert sum(1 for log in logs if log.cache_hit) == 1
    assert sum(1 for log in logs if not log.cache_hit) == 1


def test_orchestrate_multiple_services_parallel(
    client, auth_headers, configured_weather_and_news
) -> None:
    with _orchestrate_mocks(
        fetch_map={"weather": _weather_payload(), "news": _news_payload()},
    ):
        response = client.post(
            "/api/v1/orchestrate",
            headers=auth_headers,
            json={
                "services": ["weather", "news"],
                "params": {
                    "weather": {"city": "London"},
                    "news": {"query": "AI"},
                },
            },
        )

    assert response.status_code == 200
    results = {r["service"]: r for r in response.json()["results"]}
    assert results["weather"]["success"] is True
    assert results["news"]["success"] is True


def test_orchestrate_partial_failure(
    client, auth_headers, configured_weather_and_news
) -> None:
    from app.external_apis.news_api import NewsAPIClient
    from app.external_apis.weather_api import WeatherAPIClient
    from app.utils.exceptions import ExternalAPIError

    def fetch_side_effect(client, _params):
        if isinstance(client, WeatherAPIClient):
            raise ExternalAPIError("Weather API unavailable", retryable=False)
        return _news_payload()

    with _orchestrate_mocks(fetch_side_effect=fetch_side_effect):
        response = client.post(
            "/api/v1/orchestrate",
            headers=auth_headers,
            json={
                "services": ["weather", "news"],
                "params": {
                    "weather": {"city": "London"},
                    "news": {"query": "AI"},
                },
            },
        )

    assert response.status_code == 200
    results = {r["service"]: r for r in response.json()["results"]}
    assert results["weather"]["success"] is False
    assert results["news"]["success"] is True


def test_orchestrate_fans_out_in_parallel(
    client, auth_headers, configured_weather_and_news
) -> None:
    """The total time must be the slowest single call, not the sum of both."""
    import asyncio
    import time

    from app.external_apis.news_api import NewsAPIClient
    from app.external_apis.weather_api import WeatherAPIClient

    async def fetch_side_effect(client, _params):
        await asyncio.sleep(0.2)
        if isinstance(client, WeatherAPIClient):
            return _weather_payload()
        return _news_payload()

    with _orchestrate_mocks(fetch_side_effect=fetch_side_effect):
        start = time.monotonic()
        response = client.post(
            "/api/v1/orchestrate",
            headers=auth_headers,
            json={
                "services": ["weather", "news"],
                "params": {
                    "weather": {"city": "London"},
                    "news": {"query": "AI"},
                },
            },
        )
        elapsed = time.monotonic() - start

    assert response.status_code == 200
    results = response.json()["results"]
    per_service = sum(r["response_time_ms"] for r in results)
    # Sequential execution would take at least the sum of the two calls.
    assert per_service >= 400
    assert response.json()["total_time_ms"] < per_service


def test_orchestrate_rejects_invalid_params(client, auth_headers, configured_weather) -> None:
    """Params are validated against the published schema for the service."""
    with _orchestrate_mocks():
        response = client.post(
            "/api/v1/orchestrate",
            headers=auth_headers,
            json={
                "services": ["weather"],
                "params": {"weather": {"nope": "x"}},
            },
        )

    assert response.status_code == 422
    detail = response.json()["detail"]
    assert isinstance(detail, list)
    assert detail[0]["loc"][:3] == ["body", "params", "weather"]


def test_orchestrate_rejects_missing_required_params(
    client, auth_headers, configured_weather
) -> None:
    with _orchestrate_mocks():
        response = client.post(
            "/api/v1/orchestrate",
            headers=auth_headers,
            json={"services": ["weather"], "params": {"weather": {}}},
        )

    assert response.status_code == 422


def test_orchestrate_rejects_unsupported_service(client, auth_headers) -> None:
    with _orchestrate_mocks():
        response = client.post(
            "/api/v1/orchestrate",
            headers=auth_headers,
            json={"services": ["stripe"], "params": {}},
        )

    assert response.status_code == 404
    assert "Supported services" in response.json()["detail"]


def test_orchestrate_unconfigured_service_returns_404(client, auth_headers) -> None:
    with _orchestrate_mocks():
        response = client.post(
            "/api/v1/orchestrate",
            headers=auth_headers,
            json={"services": ["weather"], "params": {"weather": {"city": "London"}}},
        )
    assert response.status_code == 404


def test_orchestrate_requires_auth(client) -> None:
    response = client.post(
        "/api/v1/orchestrate",
        json={"services": ["weather"], "params": {}},
    )
    assert response.status_code == 401


def test_orchestrate_with_api_key(
    client, auth_headers, configured_weather
) -> None:
    create = client.post(
        "/api/v1/api-keys",
        headers=auth_headers,
        json={"name": "Orchestrate Key"},
    )
    raw_key = create.json()["raw_key"]

    with _orchestrate_mocks(fetch_map={"weather": _weather_payload()}):
        response = client.post(
            "/api/v1/orchestrate",
            headers={"X-API-Key": raw_key},
            json={
                "services": ["weather"],
                "params": {"weather": {"city": "Paris"}},
            },
        )

    assert response.status_code == 200
    assert response.json()["results"][0]["success"] is True
