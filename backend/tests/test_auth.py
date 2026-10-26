"""Authentication endpoint tests.

Sign-in is covered in ``test_oauth.py``. These tests cover the token
lifecycle, the profile endpoints, and the fact that the password endpoints
are gone.
"""

from jose import jwt

from app.config import get_settings


def test_get_me_authenticated(client, auth_headers) -> None:
    response = client.get("/api/v1/auth/me", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["email"] == "testuser@example.com"
    assert response.json()["tier"] == "free"


def test_get_me_no_token(client) -> None:
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_get_me_tampered_token(client) -> None:
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalid.token.here"},
    )
    assert response.status_code == 401


def test_update_profile(client, auth_headers) -> None:
    response = client.patch(
        "/api/v1/auth/me", headers=auth_headers, json={"full_name": "Renamed Person"}
    )
    assert response.status_code == 200
    assert response.json()["full_name"] == "Renamed Person"


def test_refresh_token_success(client, db, make_auth_headers) -> None:
    from app.services import session_service

    headers, user = make_auth_headers("refresh@example.com")
    refresh_token = session_service.issue_refresh_token(db, user)

    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert response.status_code == 200
    assert response.json()["access_token"]
    assert response.json()["refresh_token"]
    assert response.json()["refresh_token"] != refresh_token


def test_refresh_with_an_access_token_returns_401(client, access_token) -> None:
    response = client.post("/api/v1/auth/refresh", json={"refresh_token": access_token})
    assert response.status_code == 401


def test_logout_revokes_the_refresh_token(client, db, make_auth_headers) -> None:
    from app.services import session_service

    headers, user = make_auth_headers("logout@example.com")
    refresh_token = session_service.issue_refresh_token(db, user)

    response = client.post("/api/v1/auth/logout", json={"refresh_token": refresh_token})
    assert response.status_code == 204

    reuse = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert reuse.status_code == 401


def test_password_endpoints_are_gone(client) -> None:
    """There is no password sign-in any more."""
    for path, payload in (
        ("/api/v1/auth/register", {"email": "a@b.c", "password": "secret123", "full_name": "A"}),
        ("/api/v1/auth/login", {"email": "a@b.c", "password": "secret123"}),
        ("/api/v1/auth/change-password", {"current_password": "a", "new_password": "b"}),
        ("/api/v1/auth/forgot-password", {"email": "a@b.c"}),
        ("/api/v1/auth/reset-password", {"token": "t", "new_password": "secret123"}),
    ):
        response = client.post(path, json=payload)
        assert response.status_code == 404, f"{path} should no longer exist"


def test_jwt_payload_contains_required_claims(client, db, make_auth_headers) -> None:
    from app.services import auth_service

    headers, user = make_auth_headers("claims@example.com")
    claims = auth_service.build_token_claims(user.id, user.email, user.tier)
    token = auth_service.create_access_token(claims)

    settings = get_settings()
    payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    assert payload["type"] == "access"
    assert payload["sub"] == payload["tenant_id"]
    assert payload["email"] == "claims@example.com"
    assert payload["tier"] == "free"
