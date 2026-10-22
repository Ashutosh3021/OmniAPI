"""Rate limiting helpers for authenticated and unauthenticated requests."""

from fastapi import HTTPException, Request, status

from app.config import get_settings
from app.models.user import User
from app.services.rate_limiter import (
    RATE_LIMIT_WINDOW_SECONDS,
    RateLimiter,
    client_ip,
    identifier_hash,
)


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


def tier_name(user: User) -> str:
    """Return the user's tier label for error messages."""
    return user.tier.value if hasattr(user.tier, "value") else str(user.tier)


async def apply_rate_limit(
    request: Request,
    user: User,
    api_key_id: str = "jwt",
) -> None:
    """Enforce sliding-window rate limits and attach header values to request state."""
    limiter = RateLimiter()
    limit = get_tier_limit(user)
    allowed, remaining = await limiter.is_allowed(
        tenant_id=str(user.user_id),
        api_key_id=api_key_id,
        limit=limit,
    )

    request.state.rate_limit_limit = str(limit)
    request.state.rate_limit_remaining = str(remaining)

    if not allowed:
        retry_after = await limiter.retry_after_seconds(
            tenant_id=str(user.user_id),
            api_key_id=api_key_id,
        )
        minutes = max(1, round(retry_after / 60))
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=(
                f"Rate limit exceeded for the {tier_name(user)} tier "
                f"({limit} requests/hour). Try again in about {minutes} minute"
                f"{'s' if minutes != 1 else ''}."
            ),
            headers={
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Limit": str(limit),
                "Retry-After": str(retry_after or RATE_LIMIT_WINDOW_SECONDS),
            },
        )


async def _enforce_identifier_limit(
    scope: str,
    identifier: str,
    limit: int,
    window_seconds: int,
    message: str,
) -> None:
    """Throttle a single identifier (IP address or account) and raise on breach."""
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


async def enforce_login_rate_limit(request: Request) -> None:
    """Throttle login attempts per client IP and per target account.

    Without this, ``/auth/login`` is an unthrottled password-guessing
    endpoint — it is the only write endpoint that does not require a token.
    """
    settings = get_settings()
    window = settings.rate_limit_auth_window_seconds
    ip = client_ip(request, settings.trust_proxy_header)

    await _enforce_identifier_limit(
        scope="login_ip",
        identifier=ip,
        limit=settings.rate_limit_login_per_ip,
        window_seconds=window,
        message=(
            f"Too many sign-in attempts from this network. Try again in about "
            f"{max(1, round(window / 60))} minutes."
        ),
    )

    email = await _extract_email(request)
    if email:
        await _enforce_identifier_limit(
            scope="login_account",
            identifier=email,
            limit=settings.rate_limit_login_per_account,
            window_seconds=window,
            message=(
                "Too many sign-in attempts for this account. Try again in about "
                f"{max(1, round(window / 60))} minutes."
            ),
        )


async def enforce_register_rate_limit(request: Request) -> None:
    """Throttle account creation per client IP."""
    settings = get_settings()
    window = settings.rate_limit_auth_window_seconds
    ip = client_ip(request, settings.trust_proxy_header)

    await _enforce_identifier_limit(
        scope="register_ip",
        identifier=ip,
        limit=settings.rate_limit_register_per_ip,
        window_seconds=window,
        message=(
            "Too many accounts created from this network. Try again later."
        ),
    )


async def _extract_email(request: Request) -> str | None:
    """Read the email out of a JSON request body without consuming it."""
    try:
        body = await request.json()
    except Exception:  # noqa: BLE001 - a malformed body is handled downstream
        return None
    if isinstance(body, dict):
        email = body.get("email")
        if isinstance(email, str) and email:
            return email
    return None
