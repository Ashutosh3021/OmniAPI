"""OAuth sign-in tests.

The provider is never called: the HTTP layer is replaced with a transport
that answers like Google or GitHub would. Everything else — the state value,
the account linking, the one-time code — is the real implementation.
"""

from __future__ import annotations

from unittest.mock import patch

import fakeredis.aioredis
import httpx
import pytest

from app.services import oauth_service

GOOGLE_PROFILE = {
    "sub": "1234567890",
    "email": "person@example.com",
    "email_verified": True,
    "name": "Person Example",
    "picture": "https://example.com/avatar.png",
}

GITHUB_ACCOUNT = {
    "id": 987654321,
    "login": "person",
    "name": "Person Example",
    "email": "person@example.com",
    "avatar_url": "https://example.com/avatar.png",
}

GITHUB_EMAILS = [
    {"email": "person@example.com", "primary": True, "verified": True},
]


@pytest.fixture
def oauth_settings(monkeypatch):
    """Configure both providers for the test."""
    from app.config import get_settings

    settings = get_settings()
    monkeypatch.setattr(settings, "google_client_id", "google-client-id")
    monkeypatch.setattr(settings, "google_client_secret", "google-client-secret")
    monkeypatch.setattr(settings, "github_client_id", "github-client-id")
    monkeypatch.setattr(settings, "github_client_secret", "github-client-secret")
    monkeypatch.setattr(
        settings, "oauth_success_redirect_url", "http://localhost:3000/auth/callback"
    )
    monkeypatch.setattr(
        settings,
        "oauth_failure_redirect_url",
        "http://localhost:3000/login?error=oauth_failed",
    )
    return settings


@pytest.fixture
def fake_redis_client():
    """A Redis that actually stores values, for the state and the code."""
    return fakeredis.aioredis.FakeRedis(decode_responses=True)


@pytest.fixture
def client_with_redis(client, fake_redis_client):
    """A client whose OAuth endpoints use a working Redis."""
    with patch("app.api.v1.endpoints.auth.get_redis", return_value=fake_redis_client):
        yield client


def google_transport(profile: dict | None = None, verified: bool = True):
    """A transport that answers like Google."""
    payload = dict(profile or GOOGLE_PROFILE)
    payload["email_verified"] = verified

    def handler(request: httpx.Request) -> httpx.Response:
        host = request.url.host
        if host == "oauth2.googleapis.com":
            return httpx.Response(200, json={"access_token": "google-token"})
        if host == "openidconnect.googleapis.com":
            return httpx.Response(200, json=payload)
        return httpx.Response(404)

    return httpx.MockTransport(handler)


def github_transport(emails: list | None = None):
    """A transport that answers like GitHub."""
    entries = GITHUB_EMAILS if emails is None else emails

    def handler(request: httpx.Request) -> httpx.Response:
        host = request.url.host
        path = request.url.path
        if host == "github.com" and path == "/login/oauth/access_token":
            return httpx.Response(200, json={"access_token": "github-token"})
        if host == "api.github.com" and path == "/user":
            return httpx.Response(200, json=GITHUB_ACCOUNT)
        if host == "api.github.com" and path == "/user/emails":
            return httpx.Response(200, json=entries)
        return httpx.Response(404)

    return httpx.MockTransport(handler)


def patched_client(transport: httpx.MockTransport):
    """Patch the provider client so it uses the given transport."""
    real_client = httpx.AsyncClient

    def factory(*args, **kwargs):
        kwargs["transport"] = transport
        return real_client(*args, **kwargs)

    return patch.object(oauth_service, "provider_client", factory)


def start_and_callback(client, provider: str, state: str = "state-token") -> httpx.Response:
    """Run the callback for a provider with a known state value."""
    return client.get(
        f"/api/v1/auth/oauth/{provider}/callback",
        params={"code": "auth-code", "state": state},
        follow_redirects=False,
    )


def test_list_providers_reports_configuration(client, oauth_settings) -> None:
    response = client.get("/api/v1/auth/oauth/providers")
    assert response.status_code == 200
    providers = {item["id"]: item for item in response.json()["providers"]}
    assert set(providers) == {"google", "github"}
    assert providers["google"]["configured"] is True
    assert providers["github"]["configured"] is True


def test_start_redirects_to_the_provider(client_with_redis, oauth_settings) -> None:
    response = client_with_redis.get("/api/v1/auth/oauth/google", follow_redirects=False)
    assert response.status_code == 302
    location = response.headers["location"]
    assert location.startswith("https://accounts.google.com/o/oauth2/v2/auth")
    assert "client_id=google-client-id" in location
    assert "response_type=code" in location
    assert "state=" in location


def test_start_rejects_an_unknown_provider(client_with_redis, oauth_settings) -> None:
    response = client_with_redis.get("/api/v1/auth/oauth/myspace", follow_redirects=False)
    assert response.status_code == 401


def test_callback_creates_the_account_and_hands_back_a_code(
    client_with_redis, oauth_settings, db
) -> None:
    with patched_client(google_transport()):
        start = client_with_redis.get("/api/v1/auth/oauth/google", follow_redirects=False)
        state = start.headers["location"].split("state=")[1].split("&")[0]
        response = start_and_callback(client_with_redis, "google", state)

    assert response.status_code == 302
    location = response.headers["location"]
    assert location.startswith("http://localhost:3000/auth/callback")
    assert "code=" in location

    user = db.users.get_by_email("person@example.com")
    assert user is not None


def test_exchange_returns_a_token_pair(client_with_redis, oauth_settings, db) -> None:
    with patched_client(google_transport()):
        start = client_with_redis.get("/api/v1/auth/oauth/google", follow_redirects=False)
        state = start.headers["location"].split("state=")[1].split("&")[0]
        callback = start_and_callback(client_with_redis, "google", state)

    code = callback.headers["location"].split("code=")[1]
    response = client_with_redis.post("/api/v1/auth/oauth/exchange", json={"code": code})

    assert response.status_code == 200
    data = response.json()
    assert data["token_type"] == "bearer"
    assert data["access_token"]
    assert data["refresh_token"]

    user = db.users.get_by_email("person@example.com")
    assert user is not None
    assert user.full_name == "Person Example"

    identity = db.oauth_identities.get_by_provider("google", "1234567890")
    assert identity is not None
    assert identity.user_id == user.id


def test_exchange_code_can_only_be_used_once(client_with_redis, oauth_settings, db) -> None:
    with patched_client(google_transport()):
        start = client_with_redis.get("/api/v1/auth/oauth/google", follow_redirects=False)
        state = start.headers["location"].split("state=")[1].split("&")[0]
        callback = start_and_callback(client_with_redis, "google", state)

    code = callback.headers["location"].split("code=")[1]
    first = client_with_redis.post("/api/v1/auth/oauth/exchange", json={"code": code})
    second = client_with_redis.post("/api/v1/auth/oauth/exchange", json={"code": code})

    assert first.status_code == 200
    assert second.status_code == 401


def test_callback_rejects_an_unknown_state(client_with_redis, oauth_settings) -> None:
    with patched_client(google_transport()):
        response = start_and_callback(client_with_redis, "google", "not-a-real-state")

    assert response.status_code == 302
    assert "error=invalid_state" in response.headers["location"]


def test_callback_rejects_a_state_from_another_provider(client_with_redis, oauth_settings) -> None:
    with patched_client(google_transport()):
        start = client_with_redis.get("/api/v1/auth/oauth/google", follow_redirects=False)
        state = start.headers["location"].split("state=")[1].split("&")[0]
        response = start_and_callback(client_with_redis, "github", state)

    assert response.status_code == 302
    assert "error=invalid_state" in response.headers["location"]


def test_signing_in_twice_reuses_the_account(client_with_redis, oauth_settings, db) -> None:
    with patched_client(google_transport()):
        for _ in range(2):
            start = client_with_redis.get("/api/v1/auth/oauth/google", follow_redirects=False)
            state = start.headers["location"].split("state=")[1].split("&")[0]
            start_and_callback(client_with_redis, "google", state)

    users = db.client.execute("SELECT count(*) AS n FROM omniapi_users")
    assert users[0].rows[0][0] == 1


def test_a_second_provider_with_the_same_email_joins_the_same_account(
    client_with_redis, oauth_settings, db
) -> None:
    with patched_client(google_transport()):
        start = client_with_redis.get("/api/v1/auth/oauth/google", follow_redirects=False)
        state = start.headers["location"].split("state=")[1].split("&")[0]
        start_and_callback(client_with_redis, "google", state)

    with patched_client(github_transport()):
        start = client_with_redis.get("/api/v1/auth/oauth/github", follow_redirects=False)
        state = start.headers["location"].split("state=")[1].split("&")[0]
        start_and_callback(client_with_redis, "github", state)

    users = db.client.execute("SELECT count(*) AS n FROM omniapi_users")
    assert users[0].rows[0][0] == 1

    identities = db.client.execute(
        "SELECT provider FROM omniapi_oauth_identities ORDER BY provider"
    )
    assert [row[0] for row in identities[0].rows] == ["github", "google"]


def test_an_unverified_email_is_refused(client_with_redis, oauth_settings, db) -> None:
    with patched_client(google_transport(verified=False)):
        start = client_with_redis.get("/api/v1/auth/oauth/google", follow_redirects=False)
        state = start.headers["location"].split("state=")[1].split("&")[0]
        response = start_and_callback(client_with_redis, "google", state)

    assert response.status_code == 302
    assert "error=unverified_email" in response.headers["location"]

    users = db.client.execute("SELECT count(*) AS n FROM omniapi_users")
    assert users[0].rows[0][0] == 0


def test_a_github_account_without_a_verified_email_is_refused(
    client_with_redis, oauth_settings, db
) -> None:
    unverified = [{"email": "person@example.com", "primary": True, "verified": False}]

    with patched_client(github_transport(emails=unverified)):
        start = client_with_redis.get("/api/v1/auth/oauth/github", follow_redirects=False)
        state = start.headers["location"].split("state=")[1].split("&")[0]
        response = start_and_callback(client_with_redis, "github", state)

    assert response.status_code == 302
    assert "error=unverified_email" in response.headers["location"]

    users = db.client.execute("SELECT count(*) AS n FROM omniapi_users")
    assert users[0].rows[0][0] == 0


def test_a_provider_error_is_reported(client_with_redis, oauth_settings) -> None:
    response = client_with_redis.get(
        "/api/v1/auth/oauth/google/callback",
        params={"error": "access_denied"},
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert "error=access_denied" in response.headers["location"]
