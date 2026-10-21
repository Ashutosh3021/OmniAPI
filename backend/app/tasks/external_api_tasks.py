"""Celery tasks for external API calls.

These tasks are **not** on the request path any more — the orchestrator calls
the providers directly so the fan-out is genuinely parallel. They remain
available for ad-hoc, scheduled or manual invocations.

The task receives a ``service_id`` and reads the encrypted credential from the
database inside the worker. Passing the ciphertext as a task argument would
put every tenant's provider credentials into the broker message and the result
backend in a form that decrypts with a single key.
"""

import asyncio
import logging
from typing import Any, Type

from celery.exceptions import MaxRetriesExceededError

from app.external_apis.base import BaseAPIClient
from app.external_apis.news_api import NewsAPIClient
from app.external_apis.stock_api import StockAPIClient
from app.external_apis.weather_api import WeatherAPIClient
from app.services.service_catalog import SERVICE_CATALOG
from app.tasks.celery_app import celery_app
from app.utils.exceptions import ExternalAPIError

logger = logging.getLogger(__name__)

CLIENT_CLASSES: dict[str, Type[BaseAPIClient]] = {
    "weather": WeatherAPIClient,
    "news": NewsAPIClient,
    "stock": StockAPIClient,
}

TASK_REGISTRY = {
    "weather": "tasks.call_weather_api",
    "news": "tasks.call_news_api",
    "stock": "tasks.call_stock_api",
}


def _run_fetch(client_cls: Type[BaseAPIClient], encrypted_key: str, params: dict) -> dict:
    """Run async fetch in a sync Celery worker."""
    client = client_cls(encrypted_key)
    return asyncio.run(client.fetch(params))


def _execute_task(
    self,
    service_name: str,
    service_id: int,
    params: dict,
) -> dict[str, Any]:
    """Load the stored credential, call the provider, and normalise the result."""
    from app.db.session import SessionLocal
    from app.models.external_service import ExternalService

    client_cls = CLIENT_CLASSES[service_name]
    db = SessionLocal()
    try:
        service = db.get(ExternalService, service_id)
        if service is None:
            return {
                "success": False,
                "service": service_name,
                "data": None,
                "fetched_at": None,
                "error": f"External service {service_id} not found",
            }
        encrypted_key = service.api_key_encrypted
    finally:
        db.close()

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
        if exc.retryable:
            try:
                raise self.retry(exc=exc)
            except MaxRetriesExceededError:
                pass
        return {
            "success": False,
            "service": service_name,
            "data": None,
            "fetched_at": None,
            "error": detail,
        }
    except Exception as exc:  # noqa: BLE001 - reported to the caller
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
def call_weather_api(self, service_id: int, params: dict) -> dict[str, Any]:
    """Fetch weather data with retries on upstream failure."""
    return _execute_task(self, "weather", service_id, params)


@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=5,
    name="tasks.call_news_api",
)
def call_news_api(self, service_id: int, params: dict) -> dict[str, Any]:
    """Fetch news data with retries on upstream failure."""
    return _execute_task(self, "news", service_id, params)


@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=5,
    name="tasks.call_stock_api",
)
def call_stock_api(self, service_id: int, params: dict) -> dict[str, Any]:
    """Fetch stock data with retries on upstream failure."""
    return _execute_task(self, "stock", service_id, params)
