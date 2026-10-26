"""Sign-in through Google and GitHub.

The platform runs the OAuth handshake itself rather than delegating it to an
identity provider service. Each provider is a small, well-known contract, and
owning the flow means the session the application issues stays under the
application's control.

The shape of a sign-in is:

1. ``GET /auth/oauth/{provider}`` redirects the browser to the provider with a
   single-use ``state`` value held in Redis.
2. The provider calls back ``GET /auth/oauth/{provider}/callback``. The code is
   exchanged for the provider's profile, an identity is linked to an account,
   and a one-time code is handed to the browser.
3. The browser exchanges that code for a token pair with
   ``POST /auth/oauth/exchange``.

No token ever travels in a URL: the only thing that does is a single-use code
that expires in minutes and can be redeemed exactly once.
"""

from __future__ import annotations

import logging
import secrets
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import httpx

from app.config import Settings, get_settings
from app.db.database import Database
from app.models.user import User, UserTier
from app.utils.exceptions import AuthenticationError

logger = logging.getLogger(__name__)

GOOGLE = "google"
GITHUB = "github"

PROVIDER_NAMES = {
    GOOGLE: "Google",
    GITHUB: "GitHub",
}

# How long a sign-in attempt may take before its state value is discarded.
STATE_TTL_SECONDS = 600
# How long a one-time code stays redeemable.
CODE_TTL_SECONDS = 300

PROVIDER_TIMEOUT_SECONDS = 10.0


@dataclass(frozen=True)
class ProviderConfig:
    """Where a provider's endpoints live and what it needs."""

    id: str
    name: str
    authorize_url: str
    token_url: str
    scope: str
    client_id: str
    client_secret: str
    redirect_uri: str


@dataclass(frozen=True)
class OAuthProfile:
    """The account details a provider reports about the signed-in person."""

    provider: str
    provider_user_id: str
    email: str | None
    email_verified: bool
    display_name: str | None
    avatar_url: str | None


def provider_config(provider: str, settings: Settings | None = None) -> ProviderConfig:
    """Return the configuration for a provider.

    Raises ``AuthenticationError`` when the provider is unknown or its
    credentials are not configured.
    """
    settings = settings or get_settings()
    redirect_uri = settings.oauth_callback_url(provider)

    if provider == GOOGLE:
        if not settings.google_client_id or not settings.google_client_secret:
            raise AuthenticationError("Google sign-in is not configured")
        return ProviderConfig(
            id=GOOGLE,
            name=PROVIDER_NAMES[GOOGLE],
            authorize_url="https://accounts.google.com/o/oauth2/v2/auth",
            token_url="https://oauth2.googleapis.com/token",
            scope="openid email profile",
            client_id=settings.google_client_id,
            client_secret=settings.google_client_secret,
            redirect_uri=redirect_uri,
        )

    if provider == GITHUB:
        if not settings.github_client_id or not settings.github_client_secret:
            raise AuthenticationError("GitHub sign-in is not configured")
        return ProviderConfig(
            id=GITHUB,
            name=PROVIDER_NAMES[GITHUB],
            authorize_url="https://github.com/login/oauth/authorize",
            token_url="https://github.com/login/oauth/access_token",
            scope="read:user user:email",
            client_id=settings.github_client_id,
            client_secret=settings.github_client_secret,
            redirect_uri=redirect_uri,
        )

    raise AuthenticationError("Unknown sign-in provider")


def available_providers(settings: Settings | None = None) -> list[str]:
    """Return the providers that are configured well enough to be offered."""
    settings = settings or get_settings()
    available = []
    for provider in (GOOGLE, GITHUB):
        try:
            provider_config(provider, settings)
        except AuthenticationError:
            continue
        available.append(provider)
    return available


def authorization_url(config: ProviderConfig, state: str) -> str:
    """Build the URL the browser is sent to in order to start a sign-in."""
    return (
        f"{config.authorize_url}"
        f"?client_id={config.client_id}"
        f"&redirect_uri={config.redirect_uri}"
        f"&response_type=code"
        f"&scope={config.scope}"
        f"&state={state}"
    )


def provider_client() -> httpx.AsyncClient:
    """Return an HTTP client for talking to the providers."""
    return httpx.AsyncClient(
        timeout=PROVIDER_TIMEOUT_SECONDS,
        follow_redirects=False,
    )


async def exchange_code_for_profile(
    config: ProviderConfig,
    code: str,
    client: httpx.AsyncClient | None = None,
) -> OAuthProfile:
    """Exchange an authorization code for the provider's account profile."""
    if client is None:
        async with provider_client() as owned:
            return await exchange_code_for_profile(config, code, owned)

    response = await client.post(
        config.token_url,
        data={
            "client_id": config.client_id,
            "client_secret": config.client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": config.redirect_uri,
        },
        headers={"Accept": "application/json"},
    )
    if response.status_code >= 400:
        logger.warning(
            "%s rejected the authorization code (status %s)", config.id, response.status_code
        )
        raise AuthenticationError("Sign-in could not be completed. Please try again.")

    payload = _json_body(response)
    access_token = payload.get("access_token")
    if not access_token:
        raise AuthenticationError("Sign-in could not be completed. Please try again.")

    if config.id == GOOGLE:
        return await _google_profile(access_token, client)
    return await _github_profile(access_token, client)


async def _google_profile(access_token: str, client: httpx.AsyncClient) -> OAuthProfile:
    response = await client.get(
        "https://openidconnect.googleapis.com/v1/userinfo",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    if response.status_code >= 400:
        raise AuthenticationError("Could not read your Google profile")
    payload = _json_body(response)

    subject = payload.get("sub")
    if not subject:
        raise AuthenticationError("Could not read your Google profile")

    return OAuthProfile(
        provider=GOOGLE,
        provider_user_id=str(subject),
        email=_normalise_email(payload.get("email")),
        email_verified=bool(payload.get("email_verified")),
        display_name=payload.get("name") or payload.get("given_name"),
        avatar_url=payload.get("picture"),
    )


async def _github_profile(access_token: str, client: httpx.AsyncClient) -> OAuthProfile:
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/vnd.github+json",
    }
    response = await client.get("https://api.github.com/user", headers=headers)
    if response.status_code >= 400:
        raise AuthenticationError("Could not read your GitHub profile")
    account = _json_body(response)

    subject = account.get("id")
    if subject is None:
        raise AuthenticationError("Could not read your GitHub profile")

    email = _normalise_email(account.get("email"))
    verified = False

    # A GitHub account's own email can be private and unverified. The address
    # list is the authoritative source, so read it and pick the verified
    # primary address.
    emails_response = await client.get("https://api.github.com/user/emails", headers=headers)
    if emails_response.status_code < 400:
        entries = _json_list(emails_response)
        if entries:
            primary = next(
                (entry for entry in entries if entry.get("primary") and entry.get("verified")),
                None,
            )
            if primary is not None:
                email = _normalise_email(primary.get("email"))
                verified = True
            elif email is not None:
                verified = any(
                    entry.get("email", "").lower() == email and entry.get("verified")
                    for entry in entries
                )

    return OAuthProfile(
        provider=GITHUB,
        provider_user_id=str(subject),
        email=email,
        email_verified=verified,
        display_name=account.get("name") or account.get("login"),
        avatar_url=account.get("avatar_url"),
    )


def link_or_create_user(db: Database, profile: OAuthProfile) -> User:
    """Return the account for a provider profile, creating it when needed.

    An identity is keyed on the provider's own user id, which never changes.
    When a provider reports a verified email address that already belongs to an
    account, the identity is linked to that account instead of creating a
    second one — signing in with Google and with GitHub reaches the same
    account.

    An unverified email is refused: it is not proof that the person controls
    the mailbox, and the address is what links accounts together.
    """
    now = datetime.now(timezone.utc)

    identity = db.oauth_identities.get_by_provider(profile.provider, profile.provider_user_id)
    if identity is not None:
        user = db.users.get_by_id(identity.user_id)
        if user is None:
            raise AuthenticationError("Account is not active.")
        if not user.is_active:
            raise AuthenticationError("Account is not active.")
        db.oauth_identities.update(
            identity.id,
            email=profile.email,
            email_verified=profile.email_verified,
            display_name=profile.display_name,
            avatar_url=profile.avatar_url,
            updated_at=now,
        )
        return user

    if not profile.email:
        raise AuthenticationError(
            "Your provider account does not expose an email address. " "Add one and try again."
        )
    if not profile.email_verified:
        raise AuthenticationError(
            "Your provider account's email address is not verified. " "Verify it, then try again."
        )

    first_name, last_name = _split_name(profile.display_name)
    user = db.users.get_by_email(profile.email)
    if user is None:
        user = db.users.create(
            email=profile.email,
            first_name=first_name,
            last_name=last_name,
            tier=UserTier.FREE.value,
            created_at=now,
        )
    elif not user.is_active:
        raise AuthenticationError("Account is not active.")

    db.oauth_identities.create(
        user_id=user.id,
        provider=profile.provider,
        provider_user_id=profile.provider_user_id,
        email=profile.email,
        email_verified=profile.email_verified,
        display_name=profile.display_name,
        avatar_url=profile.avatar_url,
        created_at=now,
    )
    return user


def new_state() -> str:
    """Return a fresh, unguessable value for the OAuth ``state`` parameter."""
    return secrets.token_urlsafe(32)


def new_exchange_code() -> str:
    """Return a fresh, unguessable one-time sign-in code."""
    return secrets.token_urlsafe(32)


def _normalise_email(value: Any) -> str | None:
    """Lower-case an address so the same mailbox is one account."""
    if not isinstance(value, str):
        return None
    email = value.strip().lower()
    return email or None


def _split_name(display_name: str | None) -> tuple[str | None, str | None]:
    """Split a display name into first and last name parts."""
    if not display_name:
        return None, None
    parts = display_name.strip().split(maxsplit=1)
    if not parts:
        return None, None
    if len(parts) == 1:
        return parts[0], None
    return parts[0], parts[1]


def _json_body(response: httpx.Response) -> dict[str, Any]:
    """Parse a JSON object response body, tolerating an empty body."""
    try:
        payload = response.json()
    except ValueError:
        return {}
    return payload if isinstance(payload, dict) else {}


def _json_list(response: httpx.Response) -> list[dict[str, Any]]:
    """Parse a JSON array response body, tolerating an empty body."""
    try:
        payload = response.json()
    except ValueError:
        return []
    if not isinstance(payload, list):
        return []
    return [entry for entry in payload if isinstance(entry, dict)]
