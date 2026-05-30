"""Registry of supported external API clients (must match TASK_REGISTRY keys)."""

from app.external_apis.news_api import NewsAPIClient
from app.external_apis.stock_api import StockAPIClient
from app.external_apis.weather_api import WeatherAPIClient

CLIENT_REGISTRY: dict[str, type] = {
    "weather": WeatherAPIClient,
    "news": NewsAPIClient,
    "stock": StockAPIClient,
}
