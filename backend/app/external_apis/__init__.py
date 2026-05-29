"""External API client implementations."""

from app.external_apis.news_api import NewsAPIClient
from app.external_apis.stock_api import StockAPIClient
from app.external_apis.weather_api import WeatherAPIClient

__all__ = ["WeatherAPIClient", "NewsAPIClient", "StockAPIClient"]
