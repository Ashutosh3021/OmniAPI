"""Tests for cross-phase audit hardening fixes."""

import hashlib
import hmac
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import httpx

from app.services import api_key_service
from app.tasks.webhook_tasks import _delivery_headers, _serialize_payload, dispatch_webhook
from app.utils import encryption


def test_refresh_token_rejected_on_protected_route(client, db, make_auth_headers) -> None:
    from app.services import session_service

    headers, user = make_auth_headers("refresh@example.com")
    refresh = session_service.issue_refresh_token(db, user)

    response = client.get(
        "/api/v1/api-keys",
        headers={"Authorization": f"Bearer {refresh}"},
    )
    assert response.status_code == 401


def test_expired_api_key_rejected(client, auth_headers, db) -> None:
    create = client.post(
        "/api/v1/api-keys",
        headers=auth_headers,
        json={"name": "Expired Key"},
    )
    raw_key = create.json()["raw_key"]
    key_hash = api_key_service.hash_api_key(raw_key)
    api_key = db.api_keys.find_active_by_hash(key_hash)[0]
    db.api_keys.update(
        api_key.id,
        expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
        updated_at=datetime.now(timezone.utc),
    )

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


def test_webhook_delivery_includes_hmac_signature(db) -> None:
    from datetime import datetime, timezone

    user = db.users.create(
        email="sig@example.com",
        first_name="Sig",
        last_name="User",
        created_at=datetime.now(timezone.utc),
    )

    secret = "a" * 64
    webhook = db.webhooks.create(
        user_id=user.id,
        url="https://example.com/hook",
        event_type="orchestrate.complete",
        secret_encrypted=encryption.encrypt(secret),
        created_at=datetime.now(timezone.utc),
    )

    payload = {"event_type": "orchestrate.complete", "data": {"ok": True}}
    body = _serialize_payload(payload)
    headers = _delivery_headers(webhook, body)
    expected = hmac.new(secret.encode(), body.encode(), hashlib.sha256).hexdigest()
    assert headers["X-OmniAPI-Signature"] == f"sha256={expected}"


def test_dispatch_records_null_status_on_connect_error(db) -> None:
    user = db.users.create(
        email="conn@example.com",
        first_name="Conn",
        last_name="User",
        created_at=datetime.now(timezone.utc),
    )

    webhook = db.webhooks.create(
        user_id=user.id,
        url="https://example.com/hook",
        event_type="orchestrate.complete",
        secret_encrypted=encryption.encrypt("b" * 64),
        created_at=datetime.now(timezone.utc),
    )

    payload = {
        "event_id": "evt-1",
        "event_type": "orchestrate.complete",
        "tenant_id": str(user.id),
        "timestamp": "2026-01-01T00:00:00+00:00",
        "data": {},
    }

    original_max_retries = dispatch_webhook.max_retries
    dispatch_webhook.max_retries = 0
    try:
        with (
            patch("app.tasks.webhook_tasks.get_database", return_value=db),
            patch("app.tasks.webhook_tasks.httpx.Client") as mock_client,
        ):
            mock_client.return_value.__enter__.return_value.post.side_effect = httpx.ConnectError(
                "connection refused"
            )
            result = dispatch_webhook.run(str(webhook.id), payload)
    finally:
        dispatch_webhook.max_retries = original_max_retries

    assert result["success"] is False
    events = db.webhook_events.list_recent_for_webhook(webhook.id)
    assert len(events) == 1
    assert events[0].http_status_code is None


def test_usage_log_service_id_nullable_after_service_delete(db, test_user) -> None:
    from datetime import datetime, timezone

    service = db.external_services.create(
        user_id=test_user.id,
        service_name="weather",
        api_key_encrypted=encryption.encrypt("test-key"),
        created_at=datetime.now(timezone.utc),
    )

    db.usage_logs.insert_many(
        [
            {
                "user_id": test_user.id,
                "service_id": service.id,
                "endpoint": "/orchestrate/weather",
                "response_time_ms": 100,
                "status_code": 200,
                "cache_hit": False,
                "created_at": datetime.now(timezone.utc),
            }
        ]
    )

    db.external_services.delete(service.id)

    rows = db.client.execute("SELECT service_id FROM usage_logs WHERE user_id = " f"{test_user.id}")
    assert rows[0].rows[0][0] is None


def test_client_registry_matches_task_registry() -> None:
    from app.external_apis.registry import CLIENT_REGISTRY
    from app.tasks.external_api_tasks import TASK_REGISTRY

    assert set(CLIENT_REGISTRY.keys()) == set(TASK_REGISTRY.keys())


def test_service_catalog_matches_external_service_enum() -> None:
    """The published catalogue and the accepted enum must never drift."""
    from app.schemas.external_service import ExternalServiceName
    from app.services.service_catalog import SERVICE_CATALOG

    assert set(SERVICE_CATALOG.keys()) == {e.value for e in ExternalServiceName}
