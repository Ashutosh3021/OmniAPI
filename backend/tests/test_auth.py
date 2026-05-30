"""Authentication endpoint tests."""

from jose import jwt

from app.config import get_settings


def test_register_success(client) -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "new@example.com",
            "password": "password123",
            "full_name": "New User",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "new@example.com"
    assert data["full_name"] == "New User"
    assert data["tier"] == "free"
    assert "user_id" in data


def test_register_duplicate_email(client) -> None:
    payload = {
        "email": "dup@example.com",
        "password": "password123",
        "full_name": "Dup User",
    }
    client.post("/api/v1/auth/register", json=payload)
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 400
    assert "already" in response.json()["detail"].lower()


def test_register_weak_password(client) -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "weak@example.com",
            "password": "short",
            "full_name": "Weak User",
        },
    )
    assert response.status_code == 422


def test_login_success(client) -> None:
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "login@example.com",
            "password": "password123",
            "full_name": "Login User",
        },
    )
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "login@example.com", "password": "password123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["token_type"] == "bearer"
    assert data["access_token"]
    assert data["refresh_token"]


def test_login_wrong_password(client) -> None:
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "wrong@example.com",
            "password": "password123",
            "full_name": "Wrong User",
        },
    )
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "wrong@example.com", "password": "wrongpassword"},
    )
    assert response.status_code == 401


def test_login_nonexistent_user(client) -> None:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@example.com", "password": "password123"},
    )
    assert response.status_code == 401


def test_refresh_token_success(client) -> None:
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "refresh@example.com",
            "password": "password123",
            "full_name": "Refresh User",
        },
    )
    login = client.post(
        "/api/v1/auth/login",
        json={"email": "refresh@example.com", "password": "password123"},
    )
    refresh_token = login.json()["refresh_token"]
    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert response.status_code == 200
    assert response.json()["access_token"]
    assert response.json()["refresh_token"]


def test_refresh_with_access_token_returns_401(client, auth_headers) -> None:
    login = client.post(
        "/api/v1/auth/login",
        json={"email": "user@example.com", "password": "securepass123"},
    )
    access = login.json()["access_token"]
    response = client.post("/api/v1/auth/refresh", json={"refresh_token": access})
    assert response.status_code == 401


def test_get_me_authenticated(client, auth_headers) -> None:
    response = client.get("/api/v1/auth/me", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["email"] == "user@example.com"


def test_get_me_no_token(client) -> None:
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_get_me_tampered_token(client) -> None:
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalid.token.here"},
    )
    assert response.status_code == 401


def test_jwt_payload_contains_required_claims(client) -> None:
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "claims@example.com",
            "password": "password123",
            "full_name": "Claims User",
        },
    )
    login = client.post(
        "/api/v1/auth/login",
        json={"email": "claims@example.com", "password": "password123"},
    )
    settings = get_settings()
    payload = jwt.decode(
        login.json()["access_token"],
        settings.secret_key,
        algorithms=[settings.algorithm],
    )
    assert payload["type"] == "access"
    assert payload["sub"] == payload["tenant_id"]
    assert payload["email"] == "claims@example.com"
    assert payload["tier"] == "free"
