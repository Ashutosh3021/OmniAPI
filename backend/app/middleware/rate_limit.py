"""Rate limiting helpers for authenticated requests."""

from fastapi import HTTPException, Request, status

from app.config import get_settings
from app.models.user import User
from app.services.rate_limiter import RATE_LIMIT_WINDOW_SECONDS, RateLimiter


def get_tier_limit(user: User) -> int:
    """Return hourly request limit for the user's subscription tier."""
    settings = get_settings()
    tier = user.tier.value if hasattr(user.tier, "value") else str(user.tier)
    limits = {
        "free": settings.rate_limit_free,
        "pro": settings.rate_limit_pro,
        "enterprise": settings.rate_limit_enterprise,
    }
    return limits.get(tier, settings.rate_limit_free)


async def apply_rate_limit(
    request: Request,
    user: User,
    api_key_id: str = "jwt",
) -> None:
    """Enforce sliding-window rate limits and attach header values to request state."""
    limiter = RateLimiter()
    limit = get_tier_limit(user)
    try:
        allowed, remaining = await limiter.is_allowed(
            tenant_id=str(user.user_id),
            api_key_id=api_key_id,
            limit=limit,
        )
    finally:
        await limiter.close()

    request.state.rate_limit_limit = str(limit)
    request.state.rate_limit_remaining = str(remaining)

    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded",
            headers={
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Limit": str(limit),
                "Retry-After": str(RATE_LIMIT_WINDOW_SECONDS),
            },
        )
