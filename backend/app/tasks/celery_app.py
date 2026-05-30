"""Celery application configuration."""

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
        "app.tasks.analytics_tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    result_expires=3600,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    beat_schedule={
        "compute-hourly-stats": {
            "task": "tasks.compute_hourly_stats",
            "schedule": 3600.0,
        },
    },
)
