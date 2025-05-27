import pytest
from datetime import datetime
from app.models.user import User

def test_user_model_creation():
    user = User(
        user_id=1,
        username="testuser",
        email="testuser@example.com",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    user.set_password("mypassword")
    assert user.user_id == 1
    assert user.username == "testuser"
    assert user.check_password("mypassword") is True
    assert user.check_password("wrongpassword") is False
    assert user.email == "testuser@example.com"
    assert user.created_at is not None
    assert user.updated_at is not None

def test_user_model_str():
    user = User(
        user_id=2,
        username="anotheruser",
        email="anotheruser@example.com",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    assert str(user) == f"<User {user.username}>"
