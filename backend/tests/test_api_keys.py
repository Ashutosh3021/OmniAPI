"""API key management tests."""

from app.services import api_key_service


def test_create_api_key_returns_raw_key_once(client, auth_headers) -> None:
    response = client.post(
        "/api/v1/api-keys",
        headers=auth_headers,
        json={"name": "Production"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["raw_key"].startswith("omni_")
    assert data["name"] == "Production"
    assert "key_id" in data


def test_list_api_keys_hides_raw_key(client, auth_headers) -> None:
    create = client.post(
        "/api/v1/api-keys",
        headers=auth_headers,
        json={"name": "List Key"},
    )
    raw_key = create.json()["raw_key"]

    response = client.get("/api/v1/api-keys", headers=auth_headers)
    assert response.status_code == 200
    keys = response.json()
    assert len(keys) >= 1
    for key in keys:
        assert "raw_key" not in key
    assert raw_key not in str(keys)


def test_delete_soft_deletes_key(client, auth_headers) -> None:
    create = client.post(
        "/api/v1/api-keys",
        headers=auth_headers,
        json={"name": "To Revoke"},
    )
    key_id = create.json()["key_id"]

    delete = client.delete(f"/api/v1/api-keys/{key_id}", headers=auth_headers)
    assert delete.status_code == 204

    listing = client.get("/api/v1/api-keys", headers=auth_headers)
    revoked = next(k for k in listing.json() if k["key_id"] == key_id)
    assert revoked["is_active"] is False


def test_api_keys_require_auth(client) -> None:
    response = client.get("/api/v1/api-keys")
    assert response.status_code == 401


def test_tenant_isolation(client, db_session) -> None:
    """User B cannot revoke User A's API key."""
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "usera@example.com",
            "password": "password123",
            "full_name": "User A",
        },
    )
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "userb@example.com",
            "password": "password123",
            "full_name": "User B",
        },
    )

    login_a = client.post(
        "/api/v1/auth/login",
        json={"email": "usera@example.com", "password": "password123"},
    )
    headers_a = {"Authorization": f"Bearer {login_a.json()['access_token']}"}

    login_b = client.post(
        "/api/v1/auth/login",
        json={"email": "userb@example.com", "password": "password123"},
    )
    headers_b = {"Authorization": f"Bearer {login_b.json()['access_token']}"}

    created = client.post(
        "/api/v1/api-keys",
        headers=headers_a,
        json={"name": "User A Key"},
    )
    key_id = created.json()["key_id"]

    response = client.delete(f"/api/v1/api-keys/{key_id}", headers=headers_b)
    assert response.status_code == 404


def test_validate_api_key_returns_user(client, auth_headers, db_session) -> None:
    create = client.post(
        "/api/v1/api-keys",
        headers=auth_headers,
        json={"name": "Validate Me"},
    )
    raw_key = create.json()["raw_key"]
    user = api_key_service.validate_api_key(raw_key, db_session)
    assert user.email == "user@example.com"
