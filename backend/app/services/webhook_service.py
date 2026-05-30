"""Webhook subscription and event dispatch service."""

from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.webhook import Webhook
from app.schemas.webhook import WebhookEventPayload
from app.tasks.webhook_tasks import dispatch_webhook


class WebhookService:
    """Manage webhooks and queue delivery tasks (fire-and-forget)."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_active_webhooks(self, tenant_id: str, event_type: str) -> list[Webhook]:
        """Fetch active webhooks for a tenant matching the event type."""
        user_id = int(tenant_id)
        stmt = select(Webhook).where(
            Webhook.user_id == user_id,
            Webhook.event_type == event_type,
            Webhook.is_active.is_(True),
        )
        return list(self.db.scalars(stmt).all())

    def dispatch_event(self, tenant_id: str, event_type: str, data: dict) -> None:
        """
        Queue Celery delivery for each matching webhook.

        Does not block on HTTP delivery.
        """
        webhooks = self.get_active_webhooks(tenant_id, event_type)
        for webhook in webhooks:
            payload = WebhookEventPayload(
                event_id=str(uuid4()),
                event_type=event_type,
                tenant_id=tenant_id,
                timestamp=_utc_now_iso(),
                data=data,
            )
            dispatch_webhook.delay(
                webhook_id=str(webhook.id),
                payload=payload.model_dump(),
            )


def _utc_now_iso() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat()
