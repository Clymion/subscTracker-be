"""
Simple test helpers for creating test data.

This module provides straightforward helper functions for creating
test data without complex abstractions. Each function has a clear,
single purpose and is easy to understand.
"""

from datetime import date, timedelta
from typing import Optional

from flask import Response
from flask_jwt_extended import create_access_token, create_refresh_token
from sqlalchemy.orm import Session

from app.models.label import Label
from app.models.subscription import Subscription
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


def make_subscription(
    user_id: int,
    name: str = "Test Subscription",
    price: float = 9.99,
    currency: str = "USD",
    payment_frequency: str = "monthly",
    payment_method: str = "credit_card",
    status: str = "active",
    initial_payment_date: Optional[date] = None,
    next_payment_date: Optional[date] = None,
    **kwargs,
) -> Subscription:
    """
    Create a Subscription instance for testing.

    Args:
        user_id: ID of the user who owns the subscription.
        name: Subscription service name.
        price: Subscription price.
        currency: Currency code (USD or JPY).
        payment_frequency: Payment frequency (monthly, quarterly, yearly).
        payment_method: Payment method.
        status: Subscription status.
        initial_payment_date: Initial payment date. Defaults to today.
        next_payment_date: Next payment date. Defaults to initial_payment_date + 1 month.
        **kwargs: Additional subscription attributes.

    Returns:
        Subscription: Subscription instance ready for testing.
    """
    if initial_payment_date is None:
        initial_payment_date = date.today()

    if next_payment_date is None:
        if payment_frequency == "monthly":
            next_payment_date = initial_payment_date + timedelta(days=30)
        elif payment_frequency == "quarterly":
            next_payment_date = initial_payment_date + timedelta(days=90)
        elif payment_frequency == "yearly":
            next_payment_date = initial_payment_date + timedelta(days=365)
        else:
            next_payment_date = initial_payment_date + timedelta(days=30)

    subscription_data = {
        "user_id": user_id,
        "name": name,
        "price": price,
        "currency": currency,
        "payment_frequency": payment_frequency,
        "payment_method": payment_method,
        "status": status,
        "initial_payment_date": initial_payment_date,
        "next_payment_date": next_payment_date,
        **kwargs,
    }

    return Subscription(**subscription_data)


def save_subscription(db_session: Session, subscription: Subscription) -> Subscription:
    """
    Save a subscription to the database.

    Args:
        db_session: Database session.
        subscription: Subscription instance to save.

    Returns:
        Subscription: Saved subscription with ID assigned.
    """
    db_session.add(subscription)
    db_session.commit()
    db_session.refresh(subscription)
    return subscription


def make_and_save_subscription(
    db_session: Session, user_id: Optional[int] = None, **kwargs,
) -> Subscription:
    """
    Create and save a subscription in one step.

    Args:
        db_session: Database session.
        user_id: User ID. If None, creates a new user.
        **kwargs: Subscription attributes (passed to make_subscription).

    Returns:
        Subscription: Created and saved subscription.
    """
    if user_id is None:
        user = make_and_save_user(db_session)
        user_id = user.user_id

    subscription = make_subscription(user_id=user_id, **kwargs)
    return save_subscription(db_session, subscription)


def make_label(
    user_id: int,
    name: str = "Test Label",
    color: str = "#FF6B6B",
    parent_id: Optional[int] = None,
    system_label: bool = False,
    **kwargs,
) -> Label:
    """
    Create a Label instance for testing.

    Args:
        user_id: ID of the user who owns the label.
        name: Label name.
        color: Label color in hex format.
        parent_id: Parent label ID for hierarchy.
        system_label: Whether this is a system label.
        **kwargs: Additional label attributes.

    Returns:
        Label: Label instance ready for testing.
    """
    label_data = {
        "user_id": user_id,
        "name": name,
        "color": color,
        "parent_id": parent_id,
        "system_label": system_label,
        **kwargs,
    }

    return Label(**label_data)


def save_label(db_session: Session, label: Label) -> Label:
    """
    Save a label to the database.

    Args:
        db_session: Database session.
        label: Label instance to save.

    Returns:
        Label: Saved label with ID assigned.
    """
    db_session.add(label)
    db_session.commit()
    db_session.refresh(label)
    return label


def make_and_save_label(
    db_session: Session, user_id: Optional[int] = None, **kwargs,
) -> Label:
    """
    Create and save a label in one step.

    Args:
        db_session: Database session.
        user_id: User ID. If None, creates a new user.
        **kwargs: Label attributes (passed to make_label).

    Returns:
        Label: Created and saved label.
    """
    if user_id is None:
        user = make_and_save_user(db_session)
        user_id = user.user_id

    label = make_label(user_id=user_id, **kwargs)
    return save_label(db_session, label)


def create_label_hierarchy(
    db_session: Session,
    user_id: int,
    levels: list[tuple[str, str]],
) -> list[Label]:
    """
    Create a hierarchy of labels for testing.

    Args:
        db_session: Database session.
        user_id: User ID who owns the labels.
        levels: List of (name, color) tuples for each level.

    Returns:
        list[Label]: List of created labels in hierarchical order.

    Example:
        labels = create_label_hierarchy(
            db_session, user_id,
            [("Root", "#FF0000"), ("Child", "#00FF00"), ("Grandchild", "#0000FF")]
        )
    """
    labels = []
    parent_id = None

    for name, color in levels:
        label = make_and_save_label(
            db_session,
            user_id=user_id,
            name=name,
            color=color,
            parent_id=parent_id,
        )
        labels.append(label)
        parent_id = label.label_id

    return labels


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


def assert_subscription_matches(
    subscription: Subscription, expected_data: dict,
) -> None:
    """
    Assert that a subscription matches expected data.

    Args:
        subscription: Subscription instance to check.
        expected_data: Expected subscription data.
    """
    if "name" in expected_data:
        assert subscription.name == expected_data["name"]
    if "price" in expected_data:
        assert subscription.price == expected_data["price"]
    if "currency" in expected_data:
        assert subscription.currency == expected_data["currency"]
    if "status" in expected_data:
        assert subscription.status == expected_data["status"]
    if "user_id" in expected_data:
        assert subscription.user_id == expected_data["user_id"]


def assert_label_matches(label: Label, expected_data: dict) -> None:
    """
    Assert that a label matches expected data.

    Args:
        label: Label instance to check.
        expected_data: Expected label data.
    """
    if "name" in expected_data:
        assert label.name == expected_data["name"]
    if "color" in expected_data:
        assert label.color == expected_data["color"]
    if "user_id" in expected_data:
        assert label.user_id == expected_data["user_id"]
    if "parent_id" in expected_data:
        assert label.parent_id == expected_data["parent_id"]
    if "system_label" in expected_data:
        assert label.system_label == expected_data["system_label"]


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
        # First remove many-to-many relationships
        from app.models.association_tables import subscription_labels

        db_session.execute(subscription_labels.delete())

        # Then remove dependent entities
        from app.models.label import Label
        from app.models.subscription import Subscription

        db_session.query(Subscription).delete()
        db_session.query(Label).delete()
        db_session.query(User).delete()

        db_session.commit()
    except Exception:
        db_session.rollback()
        raise
