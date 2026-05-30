"""Celery tasks for external API calls."""

import asyncio
from typing import Any, Type

from celery.exceptions import MaxRetriesExceededError

from app.external_apis.base import BaseAPIClient
from app.external_apis.news_api import NewsAPIClient
from app.external_apis.stock_api import StockAPIClient
from app.external_apis.weather_api import WeatherAPIClient
from app.tasks.celery_app import celery_app
from app.utils.exceptions import ExternalAPIError

CLIENT_CLASSES: dict[str, Type[BaseAPIClient]] = {
    "weather": WeatherAPIClient,
    "news": NewsAPIClient,
    "stock": StockAPIClient,
}


def _run_fetch(client_cls: Type[BaseAPIClient], encrypted_key: str, params: dict) -> dict:
    """Run async fetch in a sync Celery worker."""
    client = client_cls(encrypted_key)
    return asyncio.run(client.fetch(params))


def _execute_task(
    self,
    service_name: str,
    tenant_id: str,
    encrypted_key: str,
    params: dict,
) -> dict[str, Any]:
    client_cls = CLIENT_CLASSES[service_name]
    try:
        payload = _run_fetch(client_cls, encrypted_key, params)
        return {
            "success": True,
            "service": service_name,
            "data": payload.get("data"),
            "fetched_at": payload.get("fetched_at"),
            "error": None,
        }
    except ExternalAPIError as exc:
        detail = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
        try:
            raise self.retry(exc=exc)
        except MaxRetriesExceededError:
            return {
                "success": False,
                "service": service_name,
                "data": None,
                "fetched_at": None,
                "error": detail,
            }
    except Exception as exc:
        return {
            "success": False,
            "service": service_name,
            "data": None,
            "fetched_at": None,
            "error": str(exc),
        }


@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=5,
    name="tasks.call_weather_api",
)
def call_weather_api(
    self, tenant_id: str, encrypted_key: str, params: dict
) -> dict[str, Any]:
    """Fetch weather data with retries on upstream failure."""
    return _execute_task(self, "weather", tenant_id, encrypted_key, params)


@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=5,
    name="tasks.call_news_api",
)
def call_news_api(self, tenant_id: str, encrypted_key: str, params: dict) -> dict[str, Any]:
    """Fetch news data with retries on upstream failure."""
    return _execute_task(self, "news", tenant_id, encrypted_key, params)


@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=5,
    name="tasks.call_stock_api",
)
def call_stock_api(self, tenant_id: str, encrypted_key: str, params: dict) -> dict[str, Any]:
    """Fetch stock data with retries on upstream failure."""
    return _execute_task(self, "stock", tenant_id, encrypted_key, params)
