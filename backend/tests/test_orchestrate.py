"""Orchestration endpoint tests (Phase 3 + Phase 4)."""

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
def _orchestrate_mocks(fetch_side_effect=None, cache_get_side_effect=None):
    get_kwargs: dict = {}
    if cache_get_side_effect is not None:
        get_kwargs["side_effect"] = cache_get_side_effect
    else:
        get_kwargs["return_value"] = None

    fetch_patch = patch(
        "app.tasks.external_api_tasks._run_fetch",
        side_effect=fetch_side_effect,
    )

    with (
        fetch_patch,
        patch.object(CacheService, "get", new_callable=AsyncMock, **get_kwargs),
        patch.object(CacheService, "set", new_callable=AsyncMock),
        patch.object(CacheService, "close", new_callable=AsyncMock),
        patch(
            "asyncio.to_thread",
            side_effect=lambda fn, *args, **kwargs: fn(*args, **kwargs),
        ),
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
    with _orchestrate_mocks(fetch_side_effect=[_weather_payload()]):
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

    logs = db_session.scalars(select(UsageLog)).all()
    assert len(logs) == 1
    assert logs[0].cache_hit is False


def test_orchestrate_cache_hit_on_second_request(
    client, auth_headers, configured_weather, db_session
) -> None:
    with _orchestrate_mocks(
        fetch_side_effect=[_weather_payload()],
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
        fetch_side_effect=[_weather_payload(), _news_payload()],
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

    def fetch_side_effect(client_cls, _encrypted_key, _params):
        if client_cls is WeatherAPIClient:
            raise ExternalAPIError("Weather API unavailable")
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

    with _orchestrate_mocks(fetch_side_effect=[_weather_payload()]):
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
