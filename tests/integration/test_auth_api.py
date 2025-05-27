import pytest
from flask import json

@pytest.mark.parametrize("endpoint, payload, expected_status", [
    ("/api/v1/auth/login", {"email": "test@example.com", "password": "correct_password"}, 200),
    ("/api/v1/auth/login", {"email": "wrong@example.com", "password": "wrong_password"}, 401),
    ("/api/v1/auth/register", {
        "username": "newuser",
        "email": "newuser@example.com",
        "password": "securepassword",
        "confirmPassword": "securepassword",
        "base_currency": "USD"
    }, 201),
    ("/api/v1/auth/register", {
        "username": "duplicateuser",
        "email": "existing@example.com",
        "password": "password123",
        "confirmPassword": "password123",
        "base_currency": "USD"
    }, 409),
])
def test_auth_endpoints(client, endpoint, payload, expected_status):
    response = client.post(endpoint, json=payload)
    assert response.status_code == expected_status

def test_refresh_token(client, valid_refresh_token):
    response = client.post("/api/v1/auth/refresh", json={"refresh_token": valid_refresh_token})
    assert response.status_code == 200
    data = response.get_json()
    assert "data" in data
    assert "access_token" in data["data"]
    assert "refresh_token" in data["data"]

@pytest.mark.parametrize("endpoint, method, token, expected_status", [
    ("/api/v1/users/test-user-id", "GET", "valid_access_token", 200),
    ("/api/v1/users/test-user-id", "GET", None, 401),
    ("/api/v1/users/test-user-id", "PATCH", "valid_access_token", 200),
    ("/api/v1/users/test-user-id", "DELETE", "valid_access_token", 204),
    ("/api/v1/users/test-user-id/change-password", "POST", "valid_access_token", 200),
])
def test_user_management_endpoints(client, endpoint, method, token, expected_status):
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if method == "GET":
        response = client.get(endpoint, headers=headers)
    elif method == "PATCH":
        response = client.patch(endpoint, headers=headers, json={"username": "updateduser"})
    elif method == "DELETE":
        response = client.delete(endpoint, headers=headers, json={"password": "userpassword"})
    elif method == "POST":
        response = client.post(endpoint, headers=headers, json={"current_password": "oldpass", "new_password": "newpass"})
    else:
        response = None
    assert response is not None
    assert response.status_code == expected_status
