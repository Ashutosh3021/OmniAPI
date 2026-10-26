"""Authentication endpoints: OAuth sign-in, refresh, logout, profile.

There is no password sign-in. An account is created the first time somebody
signs in with Google or GitHub, and the account is identified by the provider
account that was used.
"""

import logging
from datetime import datetime, timezone

import httpx
from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import RedirectResponse
from starlette.concurrency import run_in_threadpool

from app.config import get_settings
from app.db.database import Database, get_db
from app.middleware.auth_throttle import enforce_oauth_rate_limit
from app.models.user import User
from app.schemas.auth import (
    OAuthExchangeRequest,
    OAuthProviderInfo,
    OAuthProvidersResponse,
    Token,
    TokenRefresh,
    UserProfileUpdate,
    UserResponse,
)
from app.services import auth_service, oauth_service, session_service, user_cache
from app.services.oauth_service import PROVIDER_NAMES
from app.services.redis_client import get_redis
from app.utils.decorators import require_auth
from app.utils.exceptions import AuthenticationError
from app.utils.user_helpers import split_full_name, user_to_response

logger = logging.getLogger(__name__)

router = APIRouter()

STATE_KEY_PREFIX = "omniapi:oauth:state:"
CODE_KEY_PREFIX = "omniapi:oauth:code:"


def _issue_tokens(user: User, db: Database) -> Token:
    """Issue an access/refresh token pair for a user."""
    tier = user.tier.value if hasattr(user.tier, "value") else str(user.tier)
    claims = auth_service.build_token_claims(user.id, user.email, tier)
    refresh_token = session_service.issue_refresh_token(db, user)
    return Token(
        access_token=auth_service.create_access_token(claims),
        refresh_token=refresh_token,
    )


def _failure_redirect(error: str) -> RedirectResponse:
    """Send the browser back to the sign-in page with the reason."""
    settings = get_settings()
    base = settings.oauth_failure_redirect_url
    separator = "&" if "?" in base else "?"
    return RedirectResponse(f"{base}{separator}error={error}", status_code=status.HTTP_302_FOUND)


@router.get("/oauth/providers", response_model=OAuthProvidersResponse)
def list_oauth_providers() -> OAuthProvidersResponse:
    """Return the sign-in providers the client may offer."""
    settings = get_settings()
    providers = []
    for provider_id, name in PROVIDER_NAMES.items():
        providers.append(
            OAuthProviderInfo(
                id=provider_id,
                name=name,
                configured=provider_id in settings.oauth_providers,
            )
        )
    return OAuthProvidersResponse(providers=providers)


@router.get("/oauth/{provider}", dependencies=[Depends(enforce_oauth_rate_limit)])
async def start_oauth(provider: str, request: Request) -> RedirectResponse:
    """Redirect the browser to a provider to begin signing in.

    A single-use ``state`` value is stored against the session, so the
    provider's callback can be matched to this attempt and cannot be forged.
    """
    settings = get_settings()
    config = oauth_service.provider_config(provider, settings)

    state = oauth_service.new_state()
    redis = get_redis()
    await redis.set(
        f"{STATE_KEY_PREFIX}{state}",
        provider,
        ex=settings.oauth_state_ttl_seconds,
    )

    logger.info("Starting %s sign-in", provider)
    return RedirectResponse(
        oauth_service.authorization_url(config, state),
        status_code=status.HTTP_302_FOUND,
    )


@router.get(
    "/oauth/{provider}/callback",
    dependencies=[Depends(enforce_oauth_rate_limit)],
)
async def oauth_callback(
    provider: str,
    request: Request,
    db: Database = Depends(get_db),
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
) -> RedirectResponse:
    """Complete a provider sign-in and hand a one-time code to the browser."""
    settings = get_settings()

    if error:
        logger.info("Provider reported an error during %s sign-in: %s", provider, error)
        return _failure_redirect(error)

    if not code or not state:
        return _failure_redirect("missing_code")

    redis = get_redis()
    state_key = f"{STATE_KEY_PREFIX}{state}"
    expected_provider = await redis.get(state_key)
    # The state value is single use: it is removed whether or not it matched.
    await redis.delete(state_key)

    if not expected_provider:
        logger.warning("OAuth callback arrived with an unknown or expired state")
        return _failure_redirect("invalid_state")
    if expected_provider != provider:
        logger.warning("OAuth callback provider mismatch")
        return _failure_redirect("invalid_state")

    config = oauth_service.provider_config(provider, settings)
    try:
        profile = await oauth_service.exchange_code_for_profile(config, code)
    except AuthenticationError:
        return _failure_redirect("invalid_code")
    except httpx.HTTPError:
        logger.warning("Provider call failed during %s sign-in", provider, exc_info=True)
        return _failure_redirect("provider_unavailable")

    try:
        user = await run_in_threadpool(oauth_service.link_or_create_user, db, profile)
    except AuthenticationError as exc:
        logger.info("Rejected %s sign-in: %s", provider, exc.detail)
        return _failure_redirect("unverified_email")

    exchange_code = oauth_service.new_exchange_code()
    await redis.set(
        f"{CODE_KEY_PREFIX}{exchange_code}",
        str(user.id),
        ex=settings.oauth_code_ttl_seconds,
    )

    logger.info("Completed %s sign-in for user %s", provider, user.id)
    separator = "&" if "?" in settings.oauth_success_redirect_url else "?"
    return RedirectResponse(
        f"{settings.oauth_success_redirect_url}{separator}code={exchange_code}",
        status_code=status.HTTP_302_FOUND,
    )


@router.post("/oauth/exchange", response_model=Token)
async def exchange_oauth_code(
    body: OAuthExchangeRequest,
    db: Database = Depends(get_db),
) -> Token:
    """Exchange a one-time sign-in code for a token pair.

    The code can be redeemed exactly once, and only within a few minutes of
    being issued.
    """
    redis = get_redis()
    code_key = f"{CODE_KEY_PREFIX}{body.code}"
    raw_user_id = await redis.get(code_key)
    await redis.delete(code_key)

    if not raw_user_id:
        raise AuthenticationError("This sign-in link has expired. Please try again.")

    try:
        user_id = int(raw_user_id)
    except (TypeError, ValueError) as exc:
        raise AuthenticationError("This sign-in link has expired. Please try again.") from exc

    user = await run_in_threadpool(db.users.get_by_id, user_id)
    if user is None or not user.is_active:
        raise AuthenticationError("Account is not active.")

    tokens = await run_in_threadpool(_issue_tokens, user, db)
    await user_cache.touch_last_login(db, user)
    return tokens


@router.post("/refresh", response_model=Token)
def refresh(body: TokenRefresh, db: Database = Depends(get_db)) -> Token:
    """Exchange a refresh token for a new token pair.

    The presented token is revoked and replaced. Presenting a token that was
    already used revokes every token in the family.
    """
    user, new_refresh_token = session_service.rotate_refresh_token(db, body.refresh_token)
    tier = user.tier.value if hasattr(user.tier, "value") else str(user.tier)
    claims = auth_service.build_token_claims(user.id, user.email, tier)
    return Token(
        access_token=auth_service.create_access_token(claims),
        refresh_token=new_refresh_token,
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(body: TokenRefresh, db: Database = Depends(get_db)) -> None:
    """Revoke a refresh token. Signing out on the client is not enough."""
    session_service.revoke_refresh_token(db, body.refresh_token)


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(require_auth)) -> UserResponse:
    """Return the currently authenticated user."""
    return user_to_response(current_user)


@router.patch("/me", response_model=UserResponse)
async def update_me(
    body: UserProfileUpdate,
    db: Database = Depends(get_db),
    current_user: User = Depends(require_auth),
) -> UserResponse:
    """Update the authenticated user's profile."""
    first_name, last_name = split_full_name(body.full_name)
    updated_at = datetime.now(timezone.utc)
    user = await run_in_threadpool(
        db.users.update_profile,
        current_user.id,
        first_name=first_name,
        last_name=last_name,
        updated_at=updated_at,
    )
    if user is None:
        raise AuthenticationError("User not found")
    await user_cache.invalidate_user(user.id)
    return user_to_response(user)
