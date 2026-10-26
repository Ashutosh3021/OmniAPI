"""Celery tasks for webhook HTTP delivery."""

import hashlib
import hmac
import ipaddress
import json
import logging
import socket
from datetime import datetime, timezone
from urllib.parse import urlparse

import httpx
from celery.exceptions import MaxRetriesExceededError

from app.db.database import Database, get_database
from app.models.webhook import Webhook
from app.models.webhook_event import WebhookEventStatus
from app.tasks.celery_app import celery_app
from app.utils import encryption

logger = logging.getLogger(__name__)

RETRY_COUNTDOWNS = [10, 30, 60, 300, 600]
HTTP_TIMEOUT_SECONDS = 10.0

# A webhook that has failed this many times in a row is disabled. A single
# exhausted retry chain (or a bad afternoon on the user's endpoint) must not
# permanently kill the subscription.
MAX_CONSECUTIVE_FAILURES = 20


def _serialize_payload(payload: dict) -> str:
    return json.dumps(payload, separators=(",", ":"), sort_keys=True)


def _delivery_headers(webhook: Webhook, body: str) -> dict[str, str]:
    headers = {"Content-Type": "application/json"}
    if webhook.secret_encrypted:
        secret = encryption.decrypt(webhook.secret_encrypted)
        digest = hmac.new(secret.encode(), body.encode(), hashlib.sha256).hexdigest()
        headers["X-OmniAPI-Signature"] = f"sha256={digest}"
    return headers


def assert_deliverable_url(url: str) -> None:
    """
    Reject webhook URLs that point at internal infrastructure.

    HTTPS-only already blocks the classic plaintext metadata endpoint, but a
    hostname that resolves to a private address is still reachable from the
    worker. Redirects are not followed either, so a 302 cannot bounce the
    request to an internal address.
    """
    parsed = urlparse(url)
    if parsed.scheme != "https":
        raise ValueError("Webhook URL must use HTTPS")
    host = parsed.hostname
    if not host:
        raise ValueError("Webhook URL has no host")
    if parsed.username or parsed.password:
        raise ValueError("Webhook URL must not embed credentials")

    try:
        infos = socket.getaddrinfo(host, parsed.port or 443, proto=socket.IPPROTO_TCP)
    except socket.gaierror as exc:
        raise ValueError(f"Webhook host could not be resolved: {host}") from exc

    for info in infos:
        address = info[4][0]
        try:
            ip = ipaddress.ip_address(address)
        except ValueError:
            continue
        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_reserved
            or ip.is_multicast
            or ip.is_unspecified
        ):
            raise ValueError(f"Webhook host {host} resolves to the non-public address {address}")


def _record_attempt(
    db: Database,
    webhook: Webhook,
    payload: dict,
    *,
    attempt_number: int,
    status_code: int | None,
    success: bool,
    error_message: str | None,
) -> None:
    now = datetime.now(timezone.utc)
    db.webhook_events.create(
        webhook_id=webhook.id,
        user_id=webhook.user_id,
        event_type=payload.get("event_type", ""),
        payload=json.dumps(payload),
        status=(WebhookEventStatus.DELIVERED.value if success else WebhookEventStatus.FAILED.value),
        http_status_code=status_code,
        error_message=error_message,
        attempt_count=attempt_number,
        created_at=now,
        delivered_at=now if success else None,
    )


@celery_app.task(
    bind=True,
    max_retries=5,
    name="tasks.dispatch_webhook",
)
def dispatch_webhook(self, webhook_id: str, payload: dict) -> dict:
    """
    POST payload to the webhook URL with exponential backoff retries.

    Records each attempt in WebhookEvent. The subscription is only disabled
    after a sustained run of failures.
    """
    db = get_database()
    webhook_pk = int(webhook_id)
    attempt_number = self.request.retries + 1

    try:
        webhook = db.webhooks.get_by_id(webhook_pk)
        if webhook is None:
            return {"success": False, "error": "Webhook not found"}

        if not webhook.is_active:
            return {"success": False, "error": "Webhook inactive"}

        status_code: int | None = None
        error_message: str | None = None
        success = False

        try:
            assert_deliverable_url(webhook.url)
            body = _serialize_payload(payload)
            headers = _delivery_headers(webhook, body)
            with httpx.Client(
                timeout=HTTP_TIMEOUT_SECONDS,
                follow_redirects=False,
            ) as client:
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

            consecutive = (webhook.consecutive_failures or 0) + 1
            db.webhooks.record_attempt(
                webhook.id,
                retry_count=attempt_number,
                consecutive_failures=consecutive,
                last_triggered_at=datetime.now(timezone.utc),
            )

            if self.request.retries < self.max_retries:
                countdown = RETRY_COUNTDOWNS[min(self.request.retries, len(RETRY_COUNTDOWNS) - 1)]
                raise self.retry(exc=exc, countdown=countdown)

            # The retry chain is exhausted, but the subscription survives
            # unless failures have been sustained.
            if consecutive >= MAX_CONSECUTIVE_FAILURES:
                db.webhooks.record_attempt(
                    webhook.id,
                    retry_count=attempt_number,
                    consecutive_failures=consecutive,
                    last_triggered_at=datetime.now(timezone.utc),
                    is_active=False,
                )
            return {
                "success": False,
                "status_code": status_code,
                "attempt": attempt_number,
                "consecutive_failures": consecutive,
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
        db.webhooks.record_attempt(
            webhook.id,
            retry_count=0,
            consecutive_failures=0,
            last_triggered_at=datetime.now(timezone.utc),
        )
        return {
            "success": True,
            "status_code": status_code,
            "attempt": attempt_number,
        }
    except MaxRetriesExceededError:
        webhook = db.webhooks.get_by_id(webhook_pk)
        if webhook is not None:
            db.webhooks.record_attempt(
                webhook.id,
                retry_count=attempt_number,
                consecutive_failures=(webhook.consecutive_failures or 0) + 1,
                last_triggered_at=datetime.now(timezone.utc),
                is_active=False,
            )
        return {"success": False, "error": "Max retries exceeded"}
