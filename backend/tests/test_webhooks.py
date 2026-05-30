"""Webhook management and delivery tests."""

from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import select

from app.models.user import User, UserTier
from app.models.webhook import Webhook
from app.models.webhook_event import WebhookEvent, WebhookEventStatus
from app.tasks.webhook_tasks import dispatch_webhook


@pytest.fixture
def auth_headers(client):
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "webhook@example.com",
            "password": "securepass123",
            "full_name": "Webhook User",
        },
    )
    login = client.post(
        "/api/v1/auth/login",
        json={"email": "webhook@example.com", "password": "securepass123"},
    )
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


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


def test_dispatch_webhook_success(db_session) -> None:
    user = User(
        email="wh-user@example.com",
        password_hash="hash",
        tier=UserTier.FREE,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()

    from app.utils import encryption

    webhook = Webhook(
        user_id=user.id,
        url="https://example.com/hook",
        event_type="orchestrate.complete",
        secret_encrypted=encryption.encrypt("c" * 64),
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
        "data": {"ok": True},
    }

    mock_response = MagicMock()
    mock_response.status_code = 200

    db_session.close = MagicMock()
    with (
        patch("app.tasks.webhook_tasks.SessionLocal", return_value=db_session),
        patch("app.tasks.webhook_tasks.httpx.Client") as mock_client,
    ):
        mock_client.return_value.__enter__.return_value.post.return_value = mock_response
        result = dispatch_webhook.run(str(webhook.id), payload)

    assert result["success"] is True
    events = db_session.scalars(
        select(WebhookEvent).where(WebhookEvent.webhook_id == webhook.id)
    ).all()
    assert len(events) == 1
    assert events[0].status == WebhookEventStatus.DELIVERED


def test_webhook_disabled_after_max_retries(db_session) -> None:
    user = User(
        email="wh-fail@example.com",
        password_hash="hash",
        tier=UserTier.FREE,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()

    webhook = Webhook(
        user_id=user.id,
        url="https://example.com/hook-fail",
        event_type="orchestrate.failed",
        is_active=True,
    )
    db_session.add(webhook)
    db_session.commit()
    db_session.refresh(webhook)

    for _ in range(5):
        db_session.add(
            WebhookEvent(
                webhook_id=webhook.id,
                user_id=user.id,
                event_type="orchestrate.failed",
                payload="{}",
                status=WebhookEventStatus.FAILED,
                attempt_count=5,
            )
        )
    webhook.retry_count = 5
    webhook.is_active = False
    db_session.commit()

    db_session.refresh(webhook)
    assert webhook.is_active is False
