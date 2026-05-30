"""Redis-backed response cache for external API orchestration."""

import hashlib
import json
from typing import Any, Optional

import redis.asyncio as aioredis

from app.config import get_settings

SERVICE_TTL: dict[str, int] = {
    "weather": 3600,
    "news": 1800,
    "stock": 300,
}


class CacheService:
    """Tenant-scoped cache for normalized external API responses."""

    def __init__(self) -> None:
        settings = get_settings()
        self._redis: aioredis.Redis = aioredis.from_url(
            settings.redis_url,
            decode_responses=True,
        )

    @staticmethod
    def build_key(tenant_id: int | str, service_name: str, params: dict[str, Any]) -> str:
        """Build a deterministic, tenant-scoped cache key."""
        param_hash = hashlib.md5(
            json.dumps(params, sort_keys=True, default=str).encode()
        ).hexdigest()
        return f"omniapi:cache:{tenant_id}:{service_name}:{param_hash}"

    async def get(self, key: str) -> Optional[dict[str, Any]]:
        raw = await self._redis.get(key)
        if raw is None:
            return None
        return json.loads(raw)

    async def set(self, key: str, value: dict[str, Any], ttl_seconds: int) -> None:
        await self._redis.set(key, json.dumps(value, default=str), ex=ttl_seconds)

    async def delete(self, key: str) -> None:
        await self._redis.delete(key)

    async def exists(self, key: str) -> bool:
        return bool(await self._redis.exists(key))

    async def close(self) -> None:
        await self._redis.aclose()
