import pytest
from app.services.auth_service import AuthService
from app.models.user import User

@pytest.fixture
def auth_service():
    return AuthService()

def test_authenticate_valid_user(auth_service):
    # ここではモックやテスト用ユーザーを使う想定
    email = "test@example.com"
    password = "correct_password"
    user = auth_service.authenticate(email, password)
    assert user is not None
    assert user.email == email

def test_authenticate_invalid_user(auth_service):
    email = "wrong@example.com"
    password = "wrong_password"
    user = auth_service.authenticate(email, password)
    assert user is None

def test_register_user_valid(auth_service):
    data = {
        "username": "newuser",
        "email": "newuser@example.com",
        "password": "securepassword",
        "confirm_password": "securepassword",
        "base_currency": "USD"
    }
    user = auth_service.register_user(data)
    assert user is not None
    assert user.email == data["email"]

def test_register_user_duplicate_email(auth_service):
    data = {
        "username": "duplicateuser",
        "email": "existing@example.com",
        "password": "password123",
        "confirm_password": "password123",
        "base_currency": "USD"
    }
    with pytest.raises(ValueError):
        auth_service.register_user(data)

def test_register_user_password_mismatch(auth_service):
    data = {
        "username": "user",
        "email": "user@example.com",
        "password": "password123",
        "confirm_password": "password321",
        "base_currency": "USD"
    }
    with pytest.raises(ValueError):
        auth_service.register_user(data)
