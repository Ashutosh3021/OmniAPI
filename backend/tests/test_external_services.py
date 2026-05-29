"""External service credential endpoint tests."""

from app.utils import encryption


def test_create_external_service_encrypts_key(client, auth_headers) -> None:
    response = client.post(
        "/api/v1/external-services",
        headers=auth_headers,
        json={
            "service_name": "weather",
            "api_key": "openweather-secret-key",
            "max_calls_per_hour": 100,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["service_name"] == "weather"
    assert "api_key" not in data
    assert "api_key_encrypted" not in data


def test_list_external_services_scoped_to_user(client, auth_headers, db_session) -> None:
    client.post(
        "/api/v1/external-services",
        headers=auth_headers,
        json={"service_name": "news", "api_key": "news-secret"},
    )
    response = client.get("/api/v1/external-services", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["service_name"] == "news"


def test_duplicate_service_name_returns_400(client, auth_headers) -> None:
    payload = {"service_name": "stock", "api_key": "stock-secret"}
    client.post("/api/v1/external-services", headers=auth_headers, json=payload)
    response = client.post("/api/v1/external-services", headers=auth_headers, json=payload)
    assert response.status_code == 400


def test_encryption_roundtrip() -> None:
    plaintext = "my-secret-api-key"
    ciphertext = encryption.encrypt(plaintext)
    assert encryption.decrypt(ciphertext) == plaintext
    assert plaintext not in ciphertext
