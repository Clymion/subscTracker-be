"""
Simple test helpers for creating test data.

This module provides straightforward helper functions for creating
test data without complex abstractions. Each function has a clear,
single purpose and is easy to understand.
"""

from datetime import timedelta
from typing import Optional

from flask import Response
from flask_jwt_extended import create_access_token, create_refresh_token
from sqlalchemy.orm import Session

from app.models.user import User


def make_user(
    username: str = "testuser",
    email: str = "test@example.com",
    password: str = "testpassword123",
    **kwargs,
) -> User:
    """
    Create a User instance for testing.

    Args:
        username: User's username.
        email: User's email address.
        password: User's password (will be hashed).
        **kwargs: Additional user attributes.

    Returns:
        User: User instance ready for testing.
    """
    user_data = {
        "username": username,
        "email": email,
        **kwargs,
    }

    user = User(**user_data)
    user.set_password(password)

    return user


def save_user(db_session: Session, user: User) -> User:
    """
    Save a user to the database.

    Args:
        db_session: Database session.
        user: User instance to save.

    Returns:
        User: Saved user with ID assigned.
    """
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def make_and_save_user(db_session: Session, **kwargs) -> User:
    """
    Create and save a user in one step.

    Args:
        db_session: Database session.
        **kwargs: User attributes (passed to make_user).

    Returns:
        User: Created and saved user.
    """
    user = make_user(**kwargs)
    return save_user(db_session, user)


def make_access_token(
    user_id: str | int,
    expires_in_hours: int = 1,
) -> str:
    """
    Create a JWT access token for testing.

    Args:
        user_id: User ID for the token.
        expires_in_hours: Token expiration time in hours.

    Returns:
        str: JWT access token.
    """
    return create_access_token(
        identity=str(user_id),
        expires_delta=timedelta(hours=expires_in_hours),
    )


def make_refresh_token(user_id: str | int) -> str:
    """
    Create a JWT refresh token for testing.

    Args:
        user_id: User ID for the token.

    Returns:
        str: JWT refresh token.
    """
    return create_refresh_token(identity=str(user_id))


def make_expired_token(user_id: str | int) -> str:
    """
    Create an expired JWT token for testing expiration scenarios.

    Args:
        user_id: User ID for the token.

    Returns:
        str: Expired JWT token.
    """
    return create_access_token(
        identity=str(user_id),
        expires_delta=timedelta(seconds=-1),  # Expired 1 second ago
    )


def make_auth_headers(user_id: str | int = "testuser") -> dict[str, str]:
    """
    Create authentication headers for API testing.

    Args:
        user_id: User ID for the token.

    Returns:
        dict: Headers with Authorization bearer token.
    """
    token = make_access_token(user_id)
    return {"Authorization": f"Bearer {token}"}


def make_json_headers() -> dict[str, str]:
    """
    Create JSON content-type headers.

    Returns:
        dict: Headers with JSON content-type.
    """
    return {"Content-Type": "application/json"}


def make_api_headers(user_id: Optional[str | int] = None) -> dict[str, str]:
    """
    Create complete API headers (auth + content-type).

    Args:
        user_id: User ID for auth token. If None, no auth header.

    Returns:
        dict: Complete API headers.
    """
    headers = make_json_headers()

    if user_id is not None:
        auth_headers = make_auth_headers(user_id)
        headers.update(auth_headers)

    return headers


def make_login_data(
    email: str = "test@example.com",
    password: str = "testpassword123",
) -> dict[str, str]:
    """
    Create login request data.

    Args:
        email: User's email.
        password: User's password.

    Returns:
        dict: Login request data.
    """
    return {
        "email": email,
        "password": password,
    }


def make_registration_data(
    username: str = "newuser",
    email: str = "newuser@example.com",
    password: str = "newpassword123",
    **kwargs,
) -> dict[str, str]:
    """
    Create user registration data.

    Args:
        username: Desired username.
        email: User's email.
        password: User's password.
        **kwargs: Additional registration fields.

    Returns:
        dict: Registration request data.
    """
    return {
        "username": username,
        "email": email,
        "password": password,
        "confirm_password": password,  # Default to same as password
        "base_currency": "USD",
        **kwargs,
    }


def assert_user_matches(user: User, expected_data: dict) -> None:
    """
    Assert that a user matches expected data.

    Args:
        user: User instance to check.
        expected_data: Expected user data.
    """
    if "username" in expected_data:
        assert user.username == expected_data["username"]
    if "email" in expected_data:
        assert user.email == expected_data["email"]
    if "user_id" in expected_data:
        assert user.user_id == expected_data["user_id"]


def assert_success_response(response: Response, expected_status: int = 200) -> dict:
    """
    Assert that a response is successful and return JSON data.

    Args:
        response: Flask response object.
        expected_status: Expected HTTP status code.

    Returns:
        dict: Response JSON data.
    """
    assert response.status_code == expected_status
    assert response.content_type == "application/json"

    json_data = response.get_json()
    assert json_data is not None

    return json_data


def assert_error_response(
    response: Response,
    expected_status: int,
    expected_message: Optional[str] = None,
) -> dict:
    """
    Assert that a response contains an error.

    Args:
        response: Flask response object.
        expected_status: Expected HTTP status code.
        expected_message: Expected error message.

    Returns:
        dict: Response JSON data.
    """
    assert response.status_code == expected_status
    assert response.content_type == "application/json"

    json_data = response.get_json()
    assert json_data is not None
    assert "error" in json_data

    error_data = json_data["error"]
    assert "code" in error_data
    assert "message" in error_data

    if expected_message:
        assert error_data["message"] == expected_message

    return json_data


def clean_database(db_session: Session) -> None:
    """
    Clean all data from database tables.

    Args:
        db_session: Database session to use for cleanup.
    """
    try:
        # Delete in reverse order of dependencies
        db_session.query(User).delete()
        db_session.commit()
    except Exception:
        db_session.rollback()
        raise
