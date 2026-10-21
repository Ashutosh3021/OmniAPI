"""Process-wide shared Redis client.

The rate limiter, the response cache and the health probe all talk to the same
Redis. Constructing a client per request means a TCP connect + AUTH + teardown
on every call — against a TLS-terminated managed Redis that is a full
handshake per request. One client per process, closed on shutdown.
"""

import redis.asyncio as aioredis

from app.config import get_settings

_redis: aioredis.Redis | None = None


def get_redis() -> aioredis.Redis:
    """Return the shared async Redis client, creating it on first use."""
    global _redis
    if _redis is None:
        settings = get_settings()
        _redis = aioredis.from_url(settings.redis_url, decode_responses=True)
    return _redis


async def close_redis() -> None:
    """Close the shared Redis client. Called from the application shutdown hook."""
    global _redis
    if _redis is not None:
        await _redis.aclose()
    _redis = None
