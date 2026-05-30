"""CacheService unit tests (fakeredis, fully offline)."""

import asyncio

import pytest

from app.services.cache_service import CacheService


@pytest.fixture
async def cache_service(fake_redis, monkeypatch: pytest.MonkeyPatch) -> CacheService:
    import app.services.cache_service as cache_mod

    monkeypatch.setattr(
        cache_mod.aioredis,
        "from_url",
        lambda *args, **kwargs: fake_redis,
    )
    service = CacheService()
    yield service
    await service.close()


@pytest.mark.asyncio
@pytest.mark.uses_redis
async def test_cache_miss_returns_none(cache_service: CacheService) -> None:
    key = CacheService.build_key("tenant_1", "weather", {"city": "London"})
    assert await cache_service.get(key) is None


@pytest.mark.asyncio
@pytest.mark.uses_redis
async def test_cache_set_and_get(cache_service: CacheService) -> None:
    key = CacheService.build_key("tenant_1", "weather", {"city": "Paris"})
    value = {"service": "weather", "data": {"city": "Paris"}}
    await cache_service.set(key, value, ttl_seconds=3600)
    assert await cache_service.get(key) == value


@pytest.mark.asyncio
@pytest.mark.uses_redis
async def test_cache_respects_ttl(cache_service: CacheService) -> None:
    key = CacheService.build_key("tenant_1", "stock", {"symbol": "AAPL"})
    await cache_service.set(key, {"service": "stock"}, ttl_seconds=1)
    await asyncio.sleep(2)
    assert await cache_service.get(key) is None


@pytest.mark.asyncio
@pytest.mark.uses_redis
async def test_cache_key_is_tenant_scoped(cache_service: CacheService) -> None:
    params = {"city": "London"}
    key_a = CacheService.build_key("tenant_a", "weather", params)
    key_b = CacheService.build_key("tenant_b", "weather", params)
    assert key_a != key_b

    await cache_service.set(key_a, {"tenant": "a"}, ttl_seconds=60)
    assert await cache_service.get(key_a) is not None
    assert await cache_service.get(key_b) is None
