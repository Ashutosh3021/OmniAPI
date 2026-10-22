"""Scheduled maintenance tasks."""

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete

from app.config import get_settings
from app.db.session import SessionLocal
from app.models.usage_log import UsageLog
from app.models.webhook_event import WebhookEvent
from app.services import session_service
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="tasks.purge_old_usage_logs")
def purge_old_usage_logs() -> dict:
    """
    Delete usage and delivery history that is past its retention window.

    ``usage_logs`` grows by one row per service call and ``webhook_events``
    by one row per delivery attempt, with the full JSON payload attached.
    Without a retention job they become the largest tables in the database
    and every analytics query has to scan them.
    """
    settings = get_settings()
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        usage_cutoff = now - timedelta(days=settings.usage_log_retention_days)
        event_cutoff = now - timedelta(days=settings.webhook_event_retention_days)

        deleted_events = db.execute(
            delete(WebhookEvent).where(WebhookEvent.created_at < event_cutoff)
        ).rowcount
        db.commit()

        deleted_usage = db.execute(
            delete(UsageLog).where(UsageLog.created_at < usage_cutoff)
        ).rowcount
        db.commit()

        deleted_sessions = session_service.purge_expired(db)

        return {
            "deleted_usage_logs": int(deleted_usage or 0),
            "deleted_webhook_events": int(deleted_events or 0),
            "deleted_refresh_tokens": deleted_sessions,
        }
    except Exception:
        logger.exception("purge_old_usage_logs failed")
        return {"error": "purge failed"}
    finally:
        db.close()
