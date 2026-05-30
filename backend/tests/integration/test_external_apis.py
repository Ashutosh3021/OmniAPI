"""External API client tests with mocked HTTP (pytest-httpx)."""

import asyncio

import pytest
from pytest_httpx import HTTPXMock

from app.external_apis.news_api import NewsAPIClient
from app.external_apis.stock_api import StockAPIClient
from app.external_apis.weather_api import WeatherAPIClient
from app.utils import encryption
from app.utils.exceptions import ExternalAPIError


@pytest.fixture
def encrypted_key() -> str:
    return encryption.encrypt("fake-api-key")


def test_weather_client_normalizes_response(httpx_mock: HTTPXMock, encrypted_key: str) -> None:
    httpx_mock.add_response(
        json={
            "name": "London",
            "main": {"temp": 15.0, "humidity": 60},
            "wind": {"speed": 5.0},
            "weather": [{"description": "cloudy"}],
        }
    )
    client = WeatherAPIClient(encrypted_key)
    result = asyncio.run(client.fetch({"city": "London"}))
    assert result["service"] == "weather"
    assert result["data"]["temperature_c"] == 15.0
    assert result["data"]["city"] == "London"


def test_weather_client_raises_on_401(httpx_mock: HTTPXMock, encrypted_key: str) -> None:
    httpx_mock.add_response(status_code=401)
    client = WeatherAPIClient(encrypted_key)
    with pytest.raises(ExternalAPIError):
        asyncio.run(client.fetch({"city": "London"}))


def test_news_client_limits_to_5_articles(httpx_mock: HTTPXMock, encrypted_key: str) -> None:
    articles = [
        {
            "title": f"Article {i}",
            "source": {"name": "Source"},
            "url": f"http://example.com/{i}",
            "publishedAt": "2026-01-01",
        }
        for i in range(10)
    ]
    httpx_mock.add_response(
        json={"articles": articles, "totalResults": 10},
    )
    client = NewsAPIClient(encrypted_key)
    result = asyncio.run(client.fetch({"query": "AI"}))
    assert len(result["data"]["articles"]) == 5


def test_stock_client_normalizes_response(httpx_mock: HTTPXMock, encrypted_key: str) -> None:
    httpx_mock.add_response(
        json={
            "Global Quote": {
                "01. symbol": "AAPL",
                "05. price": "150.00",
                "09. change": "1.00",
                "10. change percent": "0.67%",
                "06. volume": "1000000",
            }
        }
    )
    client = StockAPIClient(encrypted_key)
    result = asyncio.run(client.fetch({"symbol": "AAPL"}))
    assert result["service"] == "stock"
    assert result["data"]["symbol"] == "AAPL"
    assert result["data"]["price"] == "150.00"
