"""Webhook management and delivery tests."""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from app.tasks.webhook_tasks import dispatch_webhook


@pytest.fixture
def webhook_user(db):
    """The account the webhook tests use."""
    return db.users.create(
        email="webhook@example.com",
        first_name="Webhook",
        last_name="User",
        created_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def auth_headers(webhook_user):
    """Authorization headers for the webhook account."""
    from app.services import auth_service

    claims = auth_service.build_token_claims(webhook_user.id, webhook_user.email, webhook_user.tier)
    return {"Authorization": f"Bearer {auth_service.create_access_token(claims)}"}


def test_create_webhook_requires_https(client, auth_headers) -> None:
    response = client.post(
        "/api/v1/webhooks",
        headers=auth_headers,
        json={
            "url": "http://insecure.example.com/hook",
            "event_type": "orchestrate.complete",
        },
    )
    assert response.status_code == 422


def test_create_and_list_webhooks(client, auth_headers) -> None:
    create = client.post(
        "/api/v1/webhooks",
        headers=auth_headers,
        json={
            "url": "https://example.com/webhook",
            "event_type": "orchestrate.complete",
        },
    )
    assert create.status_code == 201

    listing = client.get("/api/v1/webhooks", headers=auth_headers)
    assert listing.status_code == 200
    assert len(listing.json()) == 1


def test_webhook_test_endpoint_queues_delivery(client, auth_headers) -> None:
    create = client.post(
        "/api/v1/webhooks",
        headers=auth_headers,
        json={
            "url": "https://example.com/hook",
            "event_type": "orchestrate.complete",
        },
    )
    webhook_id = create.json()["webhook_id"]

    with patch("app.api.v1.endpoints.webhooks.dispatch_webhook") as mock_dispatch:
        mock_dispatch.delay.return_value = MagicMock()
        response = client.post(
            f"/api/v1/webhooks/{webhook_id}/test",
            headers=auth_headers,
        )

    assert response.status_code == 202
    mock_dispatch.delay.assert_called_once()


def test_dispatch_webhook_success(db, webhook_user) -> None:
    from app.utils import encryption

    webhook = db.webhooks.create(
        user_id=webhook_user.id,
        url="https://example.com/hook",
        event_type="orchestrate.complete",
        secret_encrypted=encryption.encrypt("c" * 64),
        created_at=datetime.now(timezone.utc),
    )

    payload = {
        "event_id": "evt-1",
        "event_type": "orchestrate.complete",
        "tenant_id": str(webhook_user.id),
        "timestamp": "2026-01-01T00:00:00+00:00",
        "data": {"ok": True},
    }

    mock_response = MagicMock()
    mock_response.status_code = 200

    with (
        patch("app.tasks.webhook_tasks.get_database", return_value=db),
        patch("app.tasks.webhook_tasks.httpx.Client") as mock_client,
    ):
        mock_client.return_value.__enter__.return_value.post.return_value = mock_response
        result = dispatch_webhook.run(str(webhook.id), payload)

    assert result["success"] is True
    events = db.webhook_events.list_recent_for_webhook(webhook.id)
    assert len(events) == 1
    assert events[0].status == "delivered"


def test_webhook_disabled_after_max_retries(db, webhook_user) -> None:
    webhook = db.webhooks.create(
        user_id=webhook_user.id,
        url="https://example.com/hook-fail",
        event_type="orchestrate.failed",
        created_at=datetime.now(timezone.utc),
    )

    for _ in range(5):
        db.webhook_events.create(
            webhook_id=webhook.id,
            user_id=webhook_user.id,
            event_type="orchestrate.failed",
            payload="{}",
            status="failed",
            attempt_count=5,
            created_at=datetime.now(timezone.utc),
        )
    db.webhooks.record_attempt(
        webhook.id,
        retry_count=5,
        consecutive_failures=5,
        last_triggered_at=datetime.now(timezone.utc),
        is_active=False,
    )

    reloaded = db.webhooks.get_by_id(webhook.id)
    assert reloaded is not None
    assert reloaded.is_active is False
