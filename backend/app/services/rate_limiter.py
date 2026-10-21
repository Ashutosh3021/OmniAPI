"""Redis sliding-window rate limiter per tenant, API key and service."""

import hashlib
import time
import uuid
from typing import Any, Optional

from app.services.redis_client import get_redis

RATE_LIMIT_WINDOW_SECONDS = 3600

# Trim the window, count it, and record the hit — atomically.
#
# Doing this as separate commands lets concurrent requests interleave between
# the read and the write, so N simultaneous requests all observe the same
# count and all pass the limit. A single Lua script is one round trip and
# cannot interleave.
_SLIDING_WINDOW_SCRIPT = """
local key = KEYS[1]
local window_start = ARGV[1]
local now = ARGV[2]
local limit = tonumber(ARGV[3])
local member = ARGV[4]
local window = tonumber(ARGV[5])

redis.call('ZREMRANGEBYSCORE', key, '-inf', window_start)
local count = redis.call('ZCARD', key)

if count >= limit then
  local oldest = redis.call('ZRANGE', key, 0, 0, 'WITHSCORES')
  local retry_after = window
  if oldest[2] then
    retry_after = math.ceil(tonumber(oldest[2]) + window - tonumber(now))
  end
  if retry_after < 1 then retry_after = 1 end
  return {0, 0, retry_after}
end

redis.call('ZADD', key, now, member)
redis.call('EXPIRE', key, window)
return {1, limit - count - 1, 0}
"""


class RateLimiter:
    """Sliding window rate limiter using Redis sorted sets."""

    def __init__(self) -> None:
        self._redis = get_redis()
        self._window_seconds = RATE_LIMIT_WINDOW_SECONDS

    @staticmethod
    def _key(tenant_id: str, api_key_id: str) -> str:
        return f"omniapi:rate:{tenant_id}:{api_key_id}"

    @staticmethod
    def service_key(tenant_id: str, service_id: int) -> str:
        """Key for a tenant's per-service quota (separate from the tier limit)."""
        return f"omniapi:rate:svc:{tenant_id}:{service_id}"

    @staticmethod
    def auth_key(scope: str, identifier: str) -> str:
        """Key for authentication attempt throttling (per IP or per account)."""
        return f"omniapi:rate:auth:{scope}:{identifier}"

    async def is_allowed(
        self,
        tenant_id: str,
        api_key_id: str,
        limit: int,
        window_seconds: int = RATE_LIMIT_WINDOW_SECONDS,
    ) -> tuple[bool, int]:
        """
        Check whether a request is allowed under the sliding window limit.

        Returns ``(is_allowed, requests_remaining)``.
        """
        allowed, remaining, _ = await self._consume(
            self._key(tenant_id, api_key_id), limit, window_seconds
        )
        return allowed, remaining

    async def is_allowed_service(
        self,
        tenant_id: str,
        service_id: int,
        limit: int,
        window_seconds: int = RATE_LIMIT_WINDOW_SECONDS,
    ) -> tuple[bool, int]:
        """Check a tenant's per-service quota. Returns ``(allowed, remaining)``."""
        allowed, remaining, _ = await self._consume(
            self.service_key(tenant_id, service_id), limit, window_seconds
        )
        return allowed, remaining

    async def is_allowed_identifier(
        self,
        scope: str,
        identifier: str,
        limit: int,
        window_seconds: int,
    ) -> tuple[bool, int]:
        """Throttle attempts against a single identifier (IP address or account)."""
        allowed, remaining, _ = await self._consume(
            self.auth_key(scope, identifier), limit, window_seconds
        )
        return allowed, remaining

    async def _consume(
        self,
        key: str,
        limit: int,
        window_seconds: int,
    ) -> tuple[bool, int, int]:
        """Atomically trim, count and record.

        Returns ``(allowed, remaining, retry_after_seconds)``.
        """
        now = time.time()
        window_start = now - window_seconds
        member = f"{now}-{uuid.uuid4()}"

        result = await self._redis.register_script(_SLIDING_WINDOW_SCRIPT)(
            keys=[key],
            args=[window_start, now, limit, member, window_seconds],
        )
        allowed, remaining, retry_after = (int(v) for v in result)
        return bool(allowed), remaining, retry_after

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

    async def retry_after_seconds(
        self,
        tenant_id: str,
        api_key_id: str,
        window_seconds: int = RATE_LIMIT_WINDOW_SECONDS,
    ) -> int:
        """Seconds until the oldest request in the window expires."""
        key = self._key(tenant_id, api_key_id)
        oldest = await self._redis.zrange(key, 0, 0, withscores=True)
        if not oldest:
            return 0
        return max(int(oldest[0][1] + window_seconds - time.time()), 1)

    async def close(self) -> None:
        """No-op. The Redis client is shared and closed on application shutdown."""
        return None


def identifier_hash(value: str) -> str:
    """Stable, non-reversible identifier for rate-limit keys (emails, IPs)."""
    return hashlib.sha256(value.strip().lower().encode("utf-8")).hexdigest()[:32]


def client_ip(request: Any, trust_proxy_header: bool = False) -> str:
    """Resolve the client IP, honouring X-Forwarded-For only when trusted."""
    if trust_proxy_header:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
    client = getattr(request, "client", None)
    if client is not None and getattr(client, "host", None):
        return client.host
    return "unknown"


def positive(value: Optional[int], default: int = 0) -> int:
    """Coerce an optional int to a positive int."""
    if value is None or value <= 0:
        return default
    return int(value)
