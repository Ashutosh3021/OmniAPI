"""Celery application configuration."""

import os

from celery import Celery

from app.config import get_settings

settings = get_settings()

celery_app = Celery(
    "omniapi",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=[
        "app.tasks.external_api_tasks",
        "app.tasks.webhook_tasks",
        "app.tasks.maintenance_tasks",
    ],
)

# The `solo` pool executes tasks sequentially in the worker process and
# ignores --concurrency entirely. It is only viable on Windows, where prefork
# cannot start (POSIX semaphores are unavailable). Hard-coding it made every
# deployment single-threaded while the start commands still advertised
# --concurrency=4.
if os.name == "nt":
    DEFAULT_POOL = "solo"
else:
    DEFAULT_POOL = "prefork"

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    result_expires=3600,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    # Retry broker connection on startup (suppresses CPendingDeprecationWarning in Celery 5.x)
    broker_connection_retry_on_startup=True,
    worker_pool=DEFAULT_POOL,
    # Keep the three task families on separate queues so a slow webhook
    # endpoint cannot starve maintenance work, and vice versa.
    task_routes={
        "tasks.call_weather_api": {"queue": "external"},
        "tasks.call_news_api": {"queue": "external"},
        "tasks.call_stock_api": {"queue": "external"},
        "tasks.dispatch_webhook": {"queue": "webhooks"},
        "tasks.purge_old_usage_logs": {"queue": "maintenance"},
    },
    task_default_queue="external",
    beat_schedule={
        "purge-old-usage-logs": {
            "task": "tasks.purge_old_usage_logs",
            "schedule": 3600.0 * 6,
        },
    },
)
