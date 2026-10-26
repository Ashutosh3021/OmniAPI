"""Webhook subscription management endpoints."""

import secrets
from uuid import uuid4

from fastapi import APIRouter, Depends, status

from app.db.database import Database, get_db
from app.middleware.tenant_middleware import get_tenant_id
from app.models.user import User
from app.models.webhook import Webhook
from app.models.webhook_event import WebhookEvent
from app.schemas.webhook import (
    WebhookCreate,
    WebhookCreatedResponse,
    WebhookDetailResponse,
    WebhookEventDelivery,
    WebhookEventPayload,
    WebhookResponse,
    WebhookUpdate,
)
from app.services.webhook_service import _utc_now_iso
from app.tasks.webhook_tasks import dispatch_webhook
from app.utils import encryption
from app.utils.decorators import require_auth
from app.utils.exceptions import ResourceNotFoundError

router = APIRouter()


def _to_response(webhook: Webhook) -> WebhookResponse:
    return WebhookResponse(
        webhook_id=webhook.id,
        url=webhook.url,
        event_type=webhook.event_type,
        is_active=webhook.is_active,
        retry_count=webhook.retry_count,
        created_at=webhook.created_at,
    )


def _to_event_delivery(event: WebhookEvent) -> WebhookEventDelivery:
    status_value = event.status.value if hasattr(event.status, "value") else str(event.status)
    return WebhookEventDelivery(
        event_id=event.id,
        event_type=event.event_type,
        status=status_value,
        http_status_code=event.http_status_code,
        attempt_count=event.attempt_count,
        delivered_at=event.delivered_at,
        created_at=event.created_at,
    )


@router.post("", response_model=WebhookCreatedResponse, status_code=status.HTTP_201_CREATED)
def create_webhook(
    body: WebhookCreate,
    db: Database = Depends(get_db),
    current_user: User = Depends(require_auth),
    tenant_id: str = Depends(get_tenant_id),
) -> WebhookCreatedResponse:
    _ = tenant_id
    from datetime import datetime, timezone

    signing_secret = secrets.token_hex(32)
    webhook = db.webhooks.create(
        user_id=current_user.id,
        event_type=body.event_type.value,
        url=body.url,
        secret_encrypted=encryption.encrypt(signing_secret),
        created_at=datetime.now(timezone.utc),
    )
    response = _to_response(webhook)
    return WebhookCreatedResponse(**response.model_dump(), secret=signing_secret)


@router.get("", response_model=list[WebhookResponse])
def list_webhooks(
    db: Database = Depends(get_db),
    current_user: User = Depends(require_auth),
    tenant_id: str = Depends(get_tenant_id),
) -> list[WebhookResponse]:
    _ = tenant_id
    webhooks = db.webhooks.list_for_user(current_user.id)
    return [_to_response(w) for w in webhooks]


@router.get("/{webhook_id}", response_model=WebhookDetailResponse)
def get_webhook(
    webhook_id: int,
    db: Database = Depends(get_db),
    current_user: User = Depends(require_auth),
    tenant_id: str = Depends(get_tenant_id),
) -> WebhookDetailResponse:
    _ = tenant_id
    webhook = db.webhooks.get_for_user(webhook_id, current_user.id)
    if webhook is None:
        raise ResourceNotFoundError("Webhook not found")

    recent = db.webhook_events.list_recent_for_webhook(webhook_id, limit=10)

    base = _to_response(webhook)
    return WebhookDetailResponse(
        **base.model_dump(), recent_events=[_to_event_delivery(e) for e in recent]
    )


@router.patch("/{webhook_id}", response_model=WebhookResponse)
def update_webhook(
    webhook_id: int,
    body: WebhookUpdate,
    db: Database = Depends(get_db),
    current_user: User = Depends(require_auth),
    tenant_id: str = Depends(get_tenant_id),
) -> WebhookResponse:
    _ = tenant_id
    from datetime import datetime, timezone

    if db.webhooks.get_for_user(webhook_id, current_user.id) is None:
        raise ResourceNotFoundError("Webhook not found")

    webhook = db.webhooks.update(
        webhook_id,
        url=body.url,
        is_active=body.is_active,
        updated_at=datetime.now(timezone.utc),
    )
    if webhook is None:
        raise ResourceNotFoundError("Webhook not found")

    return _to_response(webhook)


@router.delete("/{webhook_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_webhook(
    webhook_id: int,
    db: Database = Depends(get_db),
    current_user: User = Depends(require_auth),
    tenant_id: str = Depends(get_tenant_id),
) -> None:
    _ = tenant_id
    if db.webhooks.get_for_user(webhook_id, current_user.id) is None:
        raise ResourceNotFoundError("Webhook not found")

    db.webhooks.delete(webhook_id)


@router.post("/{webhook_id}/test", status_code=status.HTTP_202_ACCEPTED)
def test_webhook(
    webhook_id: int,
    db: Database = Depends(get_db),
    current_user: User = Depends(require_auth),
    tenant_id: str = Depends(get_tenant_id),
) -> dict:
    _ = tenant_id
    if db.webhooks.get_for_user(webhook_id, current_user.id) is None:
        raise ResourceNotFoundError("Webhook not found")

    payload = WebhookEventPayload(
        event_id=str(uuid4()),
        event_type="webhook.test",
        tenant_id=str(current_user.id),
        timestamp=_utc_now_iso(),
        data={"message": "OmniAPI webhook test event"},
    )
    dispatch_webhook.delay(webhook_id=str(webhook_id), payload=payload.model_dump())
    return {"status": "queued", "webhook_id": webhook_id}
