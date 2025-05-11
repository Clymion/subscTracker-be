from unittest.mock import MagicMock

import pytest


def user_factory(
    id: str = "user-id",
    username: str = "testuser",
    email: str = "test@example.com",
    role: str = "user",
):
    """Factory function to create a user dict for tests."""
    return {
        "id": id,
        "username": username,
        "email": email,
        "role": role,
    }


def assert_api_response(response, expected_status_code: int, expected_json: dict):
    """Helper to assert API response status and JSON content."""
    assert response.status_code == expected_status_code
    json_data = response.get_json()
    for key, value in expected_json.items():
        assert json_data.get(key) == value


def create_mock_function(return_value=None):
    """Create a MagicMock function with an optional return value."""
    mock_func = MagicMock()
    mock_func.return_value = return_value
    return mock_func
