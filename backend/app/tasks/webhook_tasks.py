"""Celery tasks for webhook HTTP delivery."""

import hashlib
import hmac
import json
import logging
from datetime import datetime, timezone

import httpx
from celery.exceptions import MaxRetriesExceededError
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.webhook import Webhook
from app.models.webhook_event import WebhookEvent, WebhookEventStatus
from app.tasks.celery_app import celery_app
from app.utils import encryption

logger = logging.getLogger(__name__)

RETRY_COUNTDOWNS = [10, 30, 60, 300, 600]
HTTP_TIMEOUT_SECONDS = 10.0


def _serialize_payload(payload: dict) -> str:
    return json.dumps(payload, separators=(",", ":"), sort_keys=True)


def _delivery_headers(webhook: Webhook, body: str) -> dict[str, str]:
    headers = {"Content-Type": "application/json"}
    if webhook.secret_encrypted:
        secret = encryption.decrypt(webhook.secret_encrypted)
        digest = hmac.new(secret.encode(), body.encode(), hashlib.sha256).hexdigest()
        headers["X-OmniAPI-Signature"] = f"sha256={digest}"
    return headers


def _record_attempt(
    db: Session,
    webhook: Webhook,
    payload: dict,
    *,
    attempt_number: int,
    status_code: int | None,
    success: bool,
    error_message: str | None,
) -> None:
    now = datetime.now(timezone.utc)
    db.add(
        WebhookEvent(
            webhook_id=webhook.id,
            user_id=webhook.user_id,
            event_type=payload.get("event_type", ""),
            payload=json.dumps(payload),
            status=WebhookEventStatus.DELIVERED if success else WebhookEventStatus.FAILED,
            http_status_code=status_code,
            error_message=error_message,
            attempt_count=attempt_number,
            delivered_at=now if success else None,
            created_at=now,
        )
    )
    webhook.last_triggered_at = now
    webhook.retry_count = 0 if success else attempt_number


@celery_app.task(
    bind=True,
    max_retries=5,
    name="tasks.dispatch_webhook",
)
def dispatch_webhook(self, webhook_id: str, payload: dict) -> dict:
    """
    POST payload to the webhook URL with exponential backoff retries.

    Records each attempt in WebhookEvent; disables webhook after final failure.
    """
    db = SessionLocal()
    webhook_pk = int(webhook_id)
    attempt_number = self.request.retries + 1

    try:
        webhook = db.get(Webhook, webhook_pk)
        if webhook is None:
            return {"success": False, "error": "Webhook not found"}

        if not webhook.is_active:
            return {"success": False, "error": "Webhook inactive"}

        status_code: int | None = None
        error_message: str | None = None
        success = False

        try:
            body = _serialize_payload(payload)
            headers = _delivery_headers(webhook, body)
            with httpx.Client(timeout=HTTP_TIMEOUT_SECONDS) as client:
                response = client.post(
                    webhook.url,
                    content=body.encode(),
                    headers=headers,
                )
            status_code = response.status_code
            success = status_code < 300
            if not success:
                error_message = f"HTTP {status_code}"
                raise httpx.HTTPStatusError(
                    error_message,
                    request=response.request,
                    response=response,
                )
        except Exception as exc:
            error_message = str(exc)[:500]
            if status_code is None and isinstance(exc, httpx.HTTPStatusError):
                status_code = exc.response.status_code

            _record_attempt(
                db,
                webhook,
                payload,
                attempt_number=attempt_number,
                status_code=status_code,
                success=False,
                error_message=error_message,
            )

            if self.request.retries < self.max_retries:
                countdown = RETRY_COUNTDOWNS[
                    min(self.request.retries, len(RETRY_COUNTDOWNS) - 1)
                ]
                db.commit()
                raise self.retry(exc=exc, countdown=countdown)

            webhook.is_active = False
            db.commit()
            return {
                "success": False,
                "status_code": status_code,
                "attempt": attempt_number,
            }

        _record_attempt(
            db,
            webhook,
            payload,
            attempt_number=attempt_number,
            status_code=status_code,
            success=True,
            error_message=None,
        )
        db.commit()
        return {
            "success": True,
            "status_code": status_code,
            "attempt": attempt_number,
        }
    except MaxRetriesExceededError:
        webhook = db.get(Webhook, webhook_pk)
        if webhook is not None:
            webhook.is_active = False
            db.commit()
        return {"success": False, "error": "Max retries exceeded"}
    finally:
        db.close()
