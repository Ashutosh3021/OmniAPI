"""Orchestration endpoint tests."""

from datetime import datetime, timezone
from unittest.mock import patch

import pytest
from sqlalchemy import select

from app.external_apis.news_api import NewsAPIClient
from app.external_apis.weather_api import WeatherAPIClient
from app.models.usage_log import UsageLog
from app.utils.exceptions import ExternalAPIError


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
            "articles": [{"title": "Test", "source": "Test", "url": "http://x", "published_at": "t"}],
        },
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }


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


async def _mock_weather_fetch(self, params: dict) -> dict:
    return _weather_payload()


async def _mock_news_fetch(self, params: dict) -> dict:
    return _news_payload()


async def _mock_weather_fail(self, params: dict) -> dict:
    raise ExternalAPIError("Weather API unavailable")


def test_orchestrate_weather_success(
    client, auth_headers, configured_weather, db_session
) -> None:
    with patch.object(WeatherAPIClient, "fetch", _mock_weather_fetch):
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
    assert len(data["results"]) == 1
    assert data["results"][0]["success"] is True
    assert data["results"][0]["data"]["city"] == "London"

    logs = db_session.scalars(select(UsageLog)).all()
    assert len(logs) == 1
    assert logs[0].cache_hit is False
    assert logs[0].endpoint == "/orchestrate/weather"


def test_orchestrate_multiple_services(
    client, auth_headers, configured_weather_and_news
) -> None:
    with (
        patch.object(WeatherAPIClient, "fetch", _mock_weather_fetch),
        patch.object(NewsAPIClient, "fetch", _mock_news_fetch),
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
    with (
        patch.object(WeatherAPIClient, "fetch", _mock_weather_fail),
        patch.object(NewsAPIClient, "fetch", _mock_news_fetch),
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
    assert results["weather"]["success"] is False
    assert results["news"]["success"] is True


def test_orchestrate_unconfigured_service_returns_404(client, auth_headers) -> None:
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
    client, auth_headers, configured_weather, db_session
) -> None:
    create = client.post(
        "/api/v1/api-keys",
        headers=auth_headers,
        json={"name": "Orchestrate Key"},
    )
    raw_key = create.json()["raw_key"]

    with patch.object(WeatherAPIClient, "fetch", _mock_weather_fetch):
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
