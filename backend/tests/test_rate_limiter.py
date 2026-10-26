"""Redis sliding-window rate limiter unit tests (fakeredis, fully offline)."""

import asyncio

import pytest

from app.services.rate_limiter import RateLimiter


@pytest.fixture
async def rate_limiter(fake_redis, monkeypatch: pytest.MonkeyPatch) -> RateLimiter:
    """RateLimiter backed by in-memory fake Redis."""
    import app.services.redis_client as redis_client_mod

    monkeypatch.setattr(
        redis_client_mod.aioredis,
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
        allowed, _ = await rate_limiter.is_allowed("tenant_1", "key_1", limit=5, window_seconds=60)
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
    allowed_a, _ = await rate_limiter.is_allowed("tenant_a", "same_key", limit=5, window_seconds=60)
    allowed_b, _ = await rate_limiter.is_allowed("tenant_b", "same_key", limit=5, window_seconds=60)
    assert allowed_a is False
    assert allowed_b is True


@pytest.mark.asyncio
@pytest.mark.uses_redis
async def test_concurrent_burst_respects_limit(rate_limiter: RateLimiter) -> None:
    """A burst of concurrent requests must not overshoot the limit.

    The limiter trims, counts and records in a single atomic Lua script. If
    those were separate commands, every request in the burst would observe
    the same count and all of them would be allowed.
    """
    results = await asyncio.gather(
        *(
            rate_limiter.is_allowed("tenant_burst", "key_burst", limit=10, window_seconds=60)
            for _ in range(50)
        )
    )
    allowed = [r for r, _ in results if r]
    assert len(allowed) == 10, f"expected exactly 10 allowed, got {len(allowed)}"


@pytest.mark.asyncio
@pytest.mark.uses_redis
async def test_service_quota_is_separate_from_tier_limit(
    rate_limiter: RateLimiter,
) -> None:
    """A per-service quota must not consume the tenant's tier budget."""
    for _ in range(3):
        allowed, _ = await rate_limiter.is_allowed_service(
            "tenant_svc", 42, limit=3, window_seconds=60
        )
        assert allowed is True

    allowed, _ = await rate_limiter.is_allowed_service("tenant_svc", 42, limit=3, window_seconds=60)
    assert allowed is False

    # The tier limit is untouched.
    allowed, _ = await rate_limiter.is_allowed(
        "tenant_svc", "key_svc", limit=100, window_seconds=60
    )
    assert allowed is True


@pytest.mark.asyncio
@pytest.mark.uses_redis
async def test_identifier_limit_isolated_per_identifier(
    rate_limiter: RateLimiter,
) -> None:
    for _ in range(2):
        allowed, _ = await rate_limiter.is_allowed_identifier(
            "login_ip", "1.2.3.4", limit=2, window_seconds=60
        )
        assert allowed is True

    allowed, _ = await rate_limiter.is_allowed_identifier(
        "login_ip", "1.2.3.4", limit=2, window_seconds=60
    )
    assert allowed is False

    allowed, _ = await rate_limiter.is_allowed_identifier(
        "login_ip", "5.6.7.8", limit=2, window_seconds=60
    )
    assert allowed is True
