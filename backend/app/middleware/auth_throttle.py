"""Throttling for the unauthenticated authentication endpoints.

The OAuth entry points are the only write endpoints that do not require a
token, which makes them the natural target for abuse: an attacker can drive
them from any address to burn provider quota or fill the database with
accounts. They carry their own limit, separate from the per-tenant request
quota.

This lives in its own module so the authentication throttle is not affected
by anything that patches the tenant rate limiter.
"""

from fastapi import HTTPException, Request, status

from app.config import get_settings
from app.services.rate_limiter import RateLimiter, client_ip, identifier_hash


async def _enforce(
    scope: str,
    identifier: str,
    limit: int,
    window_seconds: int,
    message: str,
) -> None:
    """Throttle a single identifier (IP address) and raise on breach."""
    limiter = RateLimiter()
    allowed, _ = await limiter.is_allowed_identifier(
        scope=scope,
        identifier=identifier_hash(identifier),
        limit=limit,
        window_seconds=window_seconds,
    )
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=message,
            headers={"Retry-After": str(window_seconds)},
        )


async def enforce_oauth_rate_limit(request: Request) -> None:
    """Throttle the OAuth entry points per client IP."""
    settings = get_settings()
    window = settings.rate_limit_auth_window_seconds
    minutes = max(1, round(window / 60))
    ip = client_ip(request, settings.trust_proxy_header)

    await _enforce(
        scope="oauth_ip",
        identifier=ip,
        limit=settings.rate_limit_oauth_per_ip,
        window_seconds=window,
        message=(
            f"Too many sign-in attempts from this network. Try again in about "
            f"{minutes} minute{'s' if minutes != 1 else ''}."
        ),
    )
