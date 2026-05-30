"""Tests for cross-phase audit hardening fixes."""

import hashlib
import hmac
import json
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import httpx
import pytest
from sqlalchemy import select

from app.models.api_key import APIKey
from app.models.external_service import ExternalService
from app.models.usage_log import UsageLog
from app.models.user import User, UserTier
from app.models.webhook import Webhook
from app.services import api_key_service, auth_service
from app.tasks.webhook_tasks import _delivery_headers, _serialize_payload, dispatch_webhook
from app.utils import encryption


def test_refresh_token_rejected_on_protected_route(client) -> None:
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "refresh@example.com",
            "password": "securepass123",
            "full_name": "Refresh User",
        },
    )
    login = client.post(
        "/api/v1/auth/login",
        json={"email": "refresh@example.com", "password": "securepass123"},
    )
    refresh = login.json()["refresh_token"]
    response = client.get(
        "/api/v1/api-keys",
        headers={"Authorization": f"Bearer {refresh}"},
    )
    assert response.status_code == 401


def test_expired_api_key_rejected(client, auth_headers, db_session) -> None:
    create = client.post(
        "/api/v1/api-keys",
        headers=auth_headers,
        json={"name": "Expired Key"},
    )
    raw_key = create.json()["raw_key"]
    key_hash = api_key_service.hash_api_key(raw_key)
    api_key = db_session.scalar(select(APIKey).where(APIKey.key_hash == key_hash))
    api_key.expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
    db_session.commit()

    response = client.post(
        "/api/v1/orchestrate",
        headers={"X-API-Key": raw_key},
        json={"services": ["weather"], "params": {}},
    )
    assert response.status_code == 401


def test_orchestrate_rejects_unknown_param_keys(client, auth_headers) -> None:
    response = client.post(
        "/api/v1/orchestrate",
        headers=auth_headers,
        json={"services": ["weather"], "params": {"news": {"q": "AI"}}},
    )
    assert response.status_code == 422


def test_webhook_create_returns_signing_secret_once(client, auth_headers) -> None:
    response = client.post(
        "/api/v1/webhooks",
        headers=auth_headers,
        json={
            "url": "https://example.com/hook",
            "event_type": "orchestrate.complete",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert "secret" in body
    assert len(body["secret"]) == 64

    listing = client.get("/api/v1/webhooks", headers=auth_headers)
    assert "secret" not in listing.json()[0]


def test_webhook_delivery_includes_hmac_signature(db_session) -> None:
    user = User(
        email="sig@example.com",
        password_hash="hash",
        tier=UserTier.FREE,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()

    secret = "a" * 64
    webhook = Webhook(
        user_id=user.id,
        url="https://example.com/hook",
        event_type="orchestrate.complete",
        secret_encrypted=encryption.encrypt(secret),
        is_active=True,
    )
    db_session.add(webhook)
    db_session.commit()

    payload = {"event_type": "orchestrate.complete", "data": {"ok": True}}
    body = _serialize_payload(payload)
    headers = _delivery_headers(webhook, body)
    expected = hmac.new(secret.encode(), body.encode(), hashlib.sha256).hexdigest()
    assert headers["X-OmniAPI-Signature"] == f"sha256={expected}"


def test_dispatch_records_null_status_on_connect_error(db_session) -> None:
    from app.models.webhook_event import WebhookEvent

    user = User(
        email="conn@example.com",
        password_hash="hash",
        tier=UserTier.FREE,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()

    webhook = Webhook(
        user_id=user.id,
        url="https://example.com/hook",
        event_type="orchestrate.complete",
        secret_encrypted=encryption.encrypt("b" * 64),
        is_active=True,
    )
    db_session.add(webhook)
    db_session.commit()
    db_session.refresh(webhook)

    payload = {
        "event_id": "evt-1",
        "event_type": "orchestrate.complete",
        "tenant_id": str(user.id),
        "timestamp": "2026-01-01T00:00:00+00:00",
        "data": {},
    }

    original_max_retries = dispatch_webhook.max_retries
    dispatch_webhook.max_retries = 0
    db_session.close = MagicMock()
    try:
        with (
            patch("app.tasks.webhook_tasks.SessionLocal", return_value=db_session),
            patch("app.tasks.webhook_tasks.httpx.Client") as mock_client,
        ):
            mock_client.return_value.__enter__.return_value.post.side_effect = (
                httpx.ConnectError("connection refused")
            )
            result = dispatch_webhook.run(str(webhook.id), payload)
    finally:
        dispatch_webhook.max_retries = original_max_retries

    assert result["success"] is False
    events = db_session.scalars(
        select(WebhookEvent).where(WebhookEvent.webhook_id == webhook.id)
    ).all()
    assert len(events) == 1
    assert events[0].http_status_code is None


def test_usage_log_service_id_nullable_after_service_delete(db_session, test_user) -> None:
    service = ExternalService(
        user_id=test_user.id,
        service_name="weather",
        api_key_encrypted=encryption.encrypt("test-key"),
    )
    db_session.add(service)
    db_session.commit()
    db_session.refresh(service)

    log = UsageLog(
        user_id=test_user.id,
        service_id=service.id,
        endpoint="/orchestrate/weather",
        response_time_ms=100,
        status_code=200,
        cache_hit=False,
    )
    db_session.add(log)
    db_session.commit()

    db_session.delete(service)
    db_session.commit()
    db_session.refresh(log)

    assert log.service_id is None


def test_client_registry_matches_task_registry() -> None:
    from app.external_apis.registry import CLIENT_REGISTRY
    from app.services.orchestrator_service import TASK_REGISTRY

    assert set(CLIENT_REGISTRY.keys()) == set(TASK_REGISTRY.keys())
