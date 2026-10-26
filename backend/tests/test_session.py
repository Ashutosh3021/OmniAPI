"""Session management: refresh token rotation, revocation and reuse detection."""

from datetime import datetime, timezone

import pytest


@pytest.fixture
def sign_in(db):
    """Create an account and return a token pair for it.

    Sign-in happens through an OAuth provider, which the tests do not call,
    so the session is issued the same way the exchange endpoint issues it.
    """

    def _sign_in(email: str = "session@example.com") -> dict:
        from app.services import auth_service, session_service

        user = db.users.create(
            email=email,
            first_name="Session",
            last_name="User",
            created_at=datetime.now(timezone.utc),
        )
        refresh_token = session_service.issue_refresh_token(db, user)
        claims = auth_service.build_token_claims(user.id, user.email, user.tier)
        return {
            "access_token": auth_service.create_access_token(claims),
            "refresh_token": refresh_token,
        }

    return _sign_in


def test_refresh_rotates_the_token(client, sign_in) -> None:
    """Refreshing must return a new refresh token and revoke the old one."""
    tokens = sign_in()

    refreshed = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": tokens["refresh_token"]},
    )
    assert refreshed.status_code == 200
    assert refreshed.json()["access_token"]
    new_refresh = refreshed.json()["refresh_token"]
    assert new_refresh != tokens["refresh_token"]


def test_old_refresh_token_is_rejected_after_rotation(client, sign_in) -> None:
    tokens = sign_in()

    first = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": tokens["refresh_token"]},
    )
    assert first.status_code == 200

    # The original token was revoked by the rotation.
    replay = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": tokens["refresh_token"]},
    )
    assert replay.status_code == 401


def test_reuse_of_revoked_token_revokes_the_family(client, sign_in) -> None:
    """Presenting a revoked token means it leaked — kill the whole family."""
    tokens = sign_in()

    first = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": tokens["refresh_token"]},
    )
    new_refresh = first.json()["refresh_token"]

    # Replay the revoked token.
    client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": tokens["refresh_token"]},
    )

    # The token issued by the rotation is now dead too.
    after = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": new_refresh},
    )
    assert after.status_code == 401


def test_refresh_requires_the_token_field(client) -> None:
    """An empty body is a 422, not a silent session reset."""
    response = client.post("/api/v1/auth/refresh", json={})
    assert response.status_code == 422


def test_logout_revokes_the_refresh_token(client, sign_in) -> None:
    tokens = sign_in()

    logged_out = client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": tokens["refresh_token"]},
    )
    assert logged_out.status_code == 204

    after = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": tokens["refresh_token"]},
    )
    assert after.status_code == 401


def test_update_profile(client, sign_in) -> None:
    tokens = sign_in()

    response = client.patch(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
        json={"full_name": "Renamed Person"},
    )
    assert response.status_code == 200
    assert response.json()["full_name"] == "Renamed Person"


def test_refresh_token_is_not_stored_in_plaintext(db, sign_in) -> None:
    tokens = sign_in()

    records = db.refresh_tokens.list_for_user(1)
    assert records
    for record in records:
        assert record.token_hash != tokens["refresh_token"]
        assert len(record.token_hash) == 64
