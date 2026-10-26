"""API key revocation, webhook failure handling and SSRF protection."""

from contextlib import contextmanager
from unittest.mock import AsyncMock, patch

import pytest

from app.tasks.webhook_tasks import MAX_CONSECUTIVE_FAILURES, assert_deliverable_url


def _create_key(client, auth_headers, name: str = "Revocable") -> tuple[int, str]:
    response = client.post("/api/v1/api-keys", headers=auth_headers, json={"name": name})
    assert response.status_code == 201
    body = response.json()
    return body["key_id"], body["raw_key"]


def _weather_fetch() -> AsyncMock:
    return AsyncMock(
        return_value={
            "service": "weather",
            "data": {"city": "London", "temperature_c": 15.0},
            "fetched_at": "2026-10-21T00:00:00Z",
        }
    )


def _key_accepted(client, raw_key: str) -> bool:
    """Whether an API key authenticates.

    ``/orchestrate`` accepts an API key. With no service configured the
    response is 404, which means authentication succeeded; a rejected key
    gives 401.
    """
    response = client.post(
        "/api/v1/orchestrate",
        headers={"X-API-Key": raw_key},
        json={"services": ["weather"], "params": {}},
    )
    return response.status_code != 401


def test_api_key_can_be_revoked(client, auth_headers) -> None:
    """Revoking keeps the record so its traffic stays attributable."""
    key_id, _ = _create_key(client, auth_headers)

    revoked = client.patch(
        f"/api/v1/api-keys/{key_id}",
        headers=auth_headers,
        json={"is_active": False},
    )
    assert revoked.status_code == 200
    assert revoked.json()["is_active"] is False

    # The key still exists, so it can still be listed and audited.
    listed = client.get("/api/v1/api-keys", headers=auth_headers).json()
    assert any(k["key_id"] == key_id for k in listed)


def test_revoked_api_key_is_rejected(client, auth_headers) -> None:
    key_id, raw_key = _create_key(client, auth_headers, "To Revoke")
    assert _key_accepted(client, raw_key) is True

    client.patch(
        f"/api/v1/api-keys/{key_id}",
        headers=auth_headers,
        json={"is_active": False},
    )

    assert _key_accepted(client, raw_key) is False


def test_revoking_one_key_leaves_the_other_working(client, auth_headers) -> None:
    first_id, first_key = _create_key(client, auth_headers, "First")
    _, second_key = _create_key(client, auth_headers, "Second")

    client.patch(
        f"/api/v1/api-keys/{first_id}",
        headers=auth_headers,
        json={"is_active": False},
    )

    assert _key_accepted(client, first_key) is False
    assert _key_accepted(client, second_key) is True


def test_usage_is_attributed_to_the_api_key(client, auth_headers, db) -> None:
    """A revoked key's traffic must still be traceable."""
    from app.db.sql import sql_literal

    _, raw_key = _create_key(client, auth_headers, "Attributed")

    with patch(
        "app.external_apis.weather_api.WeatherAPIClient.fetch",
        new=_weather_fetch(),
    ):
        client.post(
            "/api/v1/external-services",
            headers=auth_headers,
            json={"service_name": "weather", "api_key": "provider-key"},
        )
        response = client.post(
            "/api/v1/orchestrate",
            headers={"X-API-Key": raw_key},
            json={
                "services": ["weather"],
                "params": {"weather": {"city": "London"}},
            },
        )
    assert response.status_code == 200

    key_row = db.client.execute(
        f"SELECT id, user_id FROM omniapi_api_keys WHERE name = {sql_literal('Attributed')}"
    )
    key_id = key_row[0].rows[0][0]
    owner_id = key_row[0].rows[0][1]

    logs = db.client.execute(
        f"SELECT api_key_id FROM usage_logs WHERE user_id = {sql_literal(owner_id)}"
    )
    assert logs[0].rows
    assert all(row[0] == key_id for row in logs[0].rows)


# ----------------------------------------------------------------------
# Webhook failure handling
# ----------------------------------------------------------------------


def _create_webhook(client, auth_headers) -> int:
    created = client.post(
        "/api/v1/webhooks",
        headers=auth_headers,
        json={
            "url": "https://example.com/hooks",
            "event_type": "orchestrate.complete",
        },
    )
    assert created.status_code == 201
    return created.json()["webhook_id"]


@contextmanager
def _exhausted_retries(task):
    """Make the task take the "retry chain exhausted" branch.

    ``Task.request`` is a read-only property, but the ``Context`` it returns
    is mutable, so the retry counter can be set directly.
    """
    original = task.request.retries
    task.request.retries = task.max_retries
    try:
        yield
    finally:
        task.request.retries = original


def _dispatch_exhausted(db, webhook_id: int, post_side_effect, response=None):
    """Run a delivery with the retry chain already exhausted."""
    from app.tasks.webhook_tasks import dispatch_webhook

    post_patch = (
        patch("app.tasks.webhook_tasks.httpx.Client.post", return_value=response)
        if response is not None
        else patch(
            "app.tasks.webhook_tasks.httpx.Client.post",
            side_effect=post_side_effect,
        )
    )

    with (
        patch("app.tasks.webhook_tasks.get_database", return_value=db),
        _exhausted_retries(dispatch_webhook),
        post_patch,
    ):
        return dispatch_webhook.run(
            webhook_id=str(webhook_id),
            payload={"event_type": "orchestrate.complete", "data": {}},
        )


def test_single_failed_delivery_does_not_disable_the_webhook(client, auth_headers, db) -> None:
    """An exhausted retry chain must not kill the subscription."""
    webhook_id = _create_webhook(client, auth_headers)

    result = _dispatch_exhausted(db, webhook_id, ConnectionError("connection refused"))

    assert result["success"] is False
    assert result["consecutive_failures"] == 1
    assert result["consecutive_failures"] < MAX_CONSECUTIVE_FAILURES

    webhook = db.webhooks.get_by_id(webhook_id)
    assert webhook.is_active is True


def test_sustained_failures_disable_the_webhook(client, auth_headers, db) -> None:
    """After enough consecutive failures the subscription is switched off."""
    webhook_id = _create_webhook(client, auth_headers)

    for _ in range(MAX_CONSECUTIVE_FAILURES):
        _dispatch_exhausted(db, webhook_id, ConnectionError("connection refused"))

    webhook = db.webhooks.get_by_id(webhook_id)
    assert webhook.consecutive_failures >= MAX_CONSECUTIVE_FAILURES
    assert webhook.is_active is False


def test_successful_delivery_resets_the_failure_counter(client, auth_headers, db) -> None:
    webhook_id = _create_webhook(client, auth_headers)

    _dispatch_exhausted(db, webhook_id, ConnectionError("connection refused"))

    class _OkResponse:
        status_code = 200
        request = None

    result = _dispatch_exhausted(db, webhook_id, None, response=_OkResponse())

    assert result["success"] is True
    webhook = db.webhooks.get_by_id(webhook_id)
    assert webhook.consecutive_failures == 0


# ----------------------------------------------------------------------
# SSRF protection
# ----------------------------------------------------------------------


@pytest.mark.parametrize(
    "url",
    [
        "http://example.com/hook",
        "https://user:pass@example.com/hook",
    ],
)
def test_unsafe_webhook_urls_are_rejected(url: str) -> None:
    with pytest.raises(ValueError):
        assert_deliverable_url(url)


def test_loopback_webhook_url_is_rejected() -> None:
    with pytest.raises(ValueError):
        assert_deliverable_url("https://127.0.0.1/hook")


def test_private_webhook_url_is_rejected() -> None:
    with pytest.raises(ValueError):
        assert_deliverable_url("https://10.0.0.5/hook")


def test_cloud_metadata_webhook_url_is_rejected() -> None:
    with pytest.raises(ValueError):
        assert_deliverable_url("https://169.254.169.254/latest/meta-data/")
