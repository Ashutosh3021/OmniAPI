"""Phase 4 performance layer tests."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.middleware.rate_limit import apply_rate_limit, get_tier_limit
from app.models.user import User, UserTier
from app.tasks.external_api_tasks import _execute_task
from app.utils.exceptions import ExternalAPIError


@pytest.mark.asyncio
async def test_rate_limit_blocks_when_exceeded() -> None:
    user = User(
        id=1,
        email="limit@example.com",
        password_hash="x",
        tier=UserTier.FREE,
        is_active=True,
    )
    request = MagicMock()
    request.state = MagicMock()

    with patch("app.middleware.rate_limit.RateLimiter") as mock_cls:
        instance = mock_cls.return_value
        instance.is_allowed = AsyncMock(return_value=(False, 0))
        instance.close = AsyncMock()

        with pytest.raises(HTTPException) as exc_info:
            await apply_rate_limit(request, user, api_key_id="jwt")

    assert exc_info.value.status_code == 429
    assert exc_info.value.headers["X-RateLimit-Remaining"] == "0"


def test_free_tier_limit_is_100() -> None:
    user = User(
        id=1,
        email="free@example.com",
        password_hash="x",
        tier=UserTier.FREE,
        is_active=True,
    )
    assert get_tier_limit(user) == 100


def test_celery_task_retries_then_fails() -> None:
    from celery.exceptions import MaxRetriesExceededError

    task = MagicMock()
    task.max_retries = 3
    task.retry.side_effect = MaxRetriesExceededError()

    with patch("app.tasks.external_api_tasks._run_fetch") as mock_fetch:
        mock_fetch.side_effect = ExternalAPIError("upstream down")
        result = _execute_task(task, "weather", "1", "encrypted", {"city": "London"})

    assert result["success"] is False
    assert "upstream" in result["error"]


def test_orchestrate_rate_limit_429(client, auth_headers, configured_weather) -> None:
    with patch("app.middleware.rate_limit.RateLimiter") as mock_cls:
        instance = mock_cls.return_value
        instance.is_allowed = AsyncMock(return_value=(False, 0))
        instance.close = AsyncMock()

        response = client.post(
            "/api/v1/orchestrate",
            headers=auth_headers,
            json={
                "services": ["weather"],
                "params": {"weather": {"city": "London"}},
            },
        )

    assert response.status_code == 429


@pytest.fixture
def configured_weather(client, auth_headers) -> None:
    client.post(
        "/api/v1/external-services",
        headers=auth_headers,
        json={"service_name": "weather", "api_key": "weather-key"},
    )
