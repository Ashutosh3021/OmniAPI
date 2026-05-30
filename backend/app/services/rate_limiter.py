"""Redis sliding-window rate limiter per tenant and API key."""

import time
import uuid
from typing import Any

import redis.asyncio as aioredis

from app.config import get_settings

RATE_LIMIT_WINDOW_SECONDS = 3600


class RateLimiter:
    """Sliding window rate limiter using Redis sorted sets."""

    def __init__(self) -> None:
        settings = get_settings()
        self._redis: aioredis.Redis = aioredis.from_url(
            settings.redis_url,
            decode_responses=True,
        )
        self._window_seconds = RATE_LIMIT_WINDOW_SECONDS

    @staticmethod
    def _key(tenant_id: str, api_key_id: str) -> str:
        return f"omniapi:rate:{tenant_id}:{api_key_id}"

    async def is_allowed(
        self,
        tenant_id: str,
        api_key_id: str,
        limit: int,
        window_seconds: int = RATE_LIMIT_WINDOW_SECONDS,
    ) -> tuple[bool, int]:
        """
        Check whether a request is allowed under the sliding window limit.

        Returns (is_allowed, requests_remaining).
        """
        key = self._key(tenant_id, api_key_id)
        now = time.time()
        window_start = now - window_seconds

        pipe = self._redis.pipeline()
        pipe.zremrangebyscore(key, "-inf", window_start)
        pipe.zcard(key)
        results = await pipe.execute()
        current_count = int(results[1])

        if current_count >= limit:
            return False, 0

        request_id = str(uuid.uuid4())
        pipe = self._redis.pipeline()
        pipe.zadd(key, {request_id: now})
        pipe.expire(key, window_seconds)
        await pipe.execute()

        remaining = max(limit - current_count - 1, 0)
        return True, remaining

    async def get_usage(self, tenant_id: str, api_key_id: str) -> dict[str, Any]:
        """Return current window usage for a tenant/API key pair."""
        key = self._key(tenant_id, api_key_id)
        now = time.time()
        window_start = now - self._window_seconds

        await self._redis.zremrangebyscore(key, "-inf", window_start)
        count = await self._redis.zcard(key)
        return {
            "tenant_id": tenant_id,
            "api_key_id": api_key_id,
            "requests_in_window": count,
            "window_seconds": self._window_seconds,
        }

    async def close(self) -> None:
        await self._redis.aclose()
