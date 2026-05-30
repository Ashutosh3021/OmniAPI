"""Redis sliding-window rate limiter unit tests (fakeredis, fully offline)."""

import pytest

from app.services.rate_limiter import RateLimiter


@pytest.fixture
async def rate_limiter(fake_redis, monkeypatch: pytest.MonkeyPatch) -> RateLimiter:
    """RateLimiter backed by in-memory fake Redis."""
    import app.services.rate_limiter as rl_mod

    monkeypatch.setattr(
        rl_mod.aioredis,
        "from_url",
        lambda *args, **kwargs: fake_redis,
    )
    limiter = RateLimiter()
    yield limiter
    await limiter.close()


@pytest.mark.asyncio
@pytest.mark.uses_redis
async def test_rate_limit_allows_within_limit(rate_limiter: RateLimiter) -> None:
    for _ in range(5):
        allowed, _ = await rate_limiter.is_allowed(
            "tenant_1", "key_1", limit=5, window_seconds=60
        )
        assert allowed is True


@pytest.mark.asyncio
@pytest.mark.uses_redis
async def test_rate_limit_blocks_over_limit(rate_limiter: RateLimiter) -> None:
    for _ in range(5):
        await rate_limiter.is_allowed("tenant_2", "key_2", limit=5, window_seconds=60)
    allowed, remaining = await rate_limiter.is_allowed(
        "tenant_2", "key_2", limit=5, window_seconds=60
    )
    assert allowed is False
    assert remaining == 0


@pytest.mark.asyncio
@pytest.mark.uses_redis
async def test_rate_limit_isolated_per_tenant(rate_limiter: RateLimiter) -> None:
    for _ in range(5):
        await rate_limiter.is_allowed("tenant_a", "same_key", limit=5, window_seconds=60)
    allowed_a, _ = await rate_limiter.is_allowed(
        "tenant_a", "same_key", limit=5, window_seconds=60
    )
    allowed_b, _ = await rate_limiter.is_allowed(
        "tenant_b", "same_key", limit=5, window_seconds=60
    )
    assert allowed_a is False
    assert allowed_b is True
