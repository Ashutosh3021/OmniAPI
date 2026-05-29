"""Authentication endpoint tests."""

from jose import jwt

from app.config import get_settings


def test_register_creates_user(client) -> None:
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


def test_register_duplicate_email_returns_400(client) -> None:
    payload = {
        "email": "dup@example.com",
        "password": "password123",
        "full_name": "Dup User",
    }
    client.post("/api/v1/auth/register", json=payload)
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 400
    assert "already" in response.json()["detail"].lower()


def test_login_returns_tokens(client) -> None:
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


def test_login_wrong_password_returns_401(client) -> None:
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


def test_refresh_returns_new_tokens(client) -> None:
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


def test_me_returns_current_user(client, auth_headers) -> None:
    response = client.get("/api/v1/auth/me", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["email"] == "user@example.com"


def test_me_without_token_returns_401(client) -> None:
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_tampered_token_returns_401(client) -> None:
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
