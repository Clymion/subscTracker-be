"""
API tests for authentication endpoints.

Simple, straightforward API tests without complex abstractions.
Each test clearly shows what HTTP request is made and what response is expected.
"""

from collections.abc import Generator

import pytest
from flask.testing import FlaskClient
from sqlalchemy.orm import Session

from app.constants import ErrorMessages
from tests.helpers import (
    assert_error_response,
    assert_success_response,
    make_and_save_user,
    make_api_headers,
    make_login_data,
    make_registration_data,
)


@pytest.fixture
def authenticated_user_with_tokens(
    client: FlaskClient,
    clean_db: Generator[Session, None, None],
) -> dict[str, str | dict]:
    """
    Create authenticated user with access and refresh tokens via API.

    Args:
        client: Flask test client.
        clean_db: Clean database session.

    Returns:
        dict: User data with tokens from actual API response.
    """
    # Create user in database
    user = make_and_save_user(
        clean_db,
        username="tokenuser",
        email="token@example.com",
        password="tokenpassword123",
    )

    # Login to get real tokens from API
    login_data = make_login_data(
        email="token@example.com",
        password="tokenpassword123",
    )

    response = client.post(
        "/api/v1/auth/login",
        json=login_data,
        headers=make_api_headers(),
    )

    login_response_data = assert_success_response(response, expected_status=200)

    return {
        "user": user,
        "access_token": login_response_data["token"],
        "refresh_token": login_response_data["refresh_token"],
        "headers": {"Authorization": f"Bearer {login_response_data['token']}"},
    }


@pytest.mark.api
@pytest.mark.auth
class TestLoginAPI:
    """Test /api/v1/auth/login endpoint."""

    def test_login_with_valid_credentials(
        self,
        client: FlaskClient,
        clean_db: Generator[Session, None, None],
    ):
        """Test successful login with correct email and password."""
        # Arrange: Create user and prepare login data
        user = make_and_save_user(
            clean_db,
            email="test@example.com",
            password="testpassword123",
        )
        login_data = make_login_data(email=user.email, password="testpassword123")
        headers = make_api_headers()

        # Act: Make login request
        response = client.post("/api/v1/auth/login", json=login_data, headers=headers)

        # Assert: Should return success with token and user data
        data = assert_success_response(response, expected_status=200)
        assert "token" in data
        assert "refresh_token" in data
        assert "user" in data
        assert data["user"]["email"] == user.email
        assert data["user"]["username"] == user.username

    def test_login_with_invalid_email(
        self,
        client: FlaskClient,
        clean_db: Generator[Session, None, None],
    ):
        """Test login failure with non-existent email."""
        # Arrange: Don't create any user, try to login
        login_data = make_login_data(email="nonexistent@example.com")
        headers = make_api_headers()

        # Act: Make login request
        response = client.post("/api/v1/auth/login", json=login_data, headers=headers)

        # Assert: Should return 401 unauthorized
        assert_error_response(
            response,
            expected_status=401,
            expected_message=ErrorMessages.INVALID_CREDENTIALS,
        )

    def test_login_with_wrong_password(
        self,
        client: FlaskClient,
        clean_db: Generator[Session, None, None],
    ):
        """Test login failure with incorrect password."""
        # Arrange: Create user with known password
        user = make_and_save_user(
            clean_db,
            email="test@example.com",
            password="correctpassword",
        )
        login_data = make_login_data(email=user.email, password="wrongpassword")
        headers = make_api_headers()

        # Act: Make login request
        response = client.post("/api/v1/auth/login", json=login_data, headers=headers)

        # Assert: Should return 401 unauthorized
        assert_error_response(
            response,
            expected_status=401,
            expected_message=ErrorMessages.INVALID_CREDENTIALS,
        )

    def test_login_with_missing_email(self, client: FlaskClient):
        """Test login failure when email is missing."""
        # Arrange: Prepare login data without email
        login_data = {"password": "somepassword"}
        headers = make_api_headers()

        # Act: Make login request
        response = client.post("/api/v1/auth/login", json=login_data, headers=headers)

        # Assert: Should return error
        assert response.status_code >= 400

    def test_login_with_missing_password(self, client: FlaskClient):
        """Test login failure when password is missing."""
        # Arrange: Prepare login data without password
        login_data = {"email": "test@example.com"}
        headers = make_api_headers()

        # Act: Make login request
        response = client.post("/api/v1/auth/login", json=login_data, headers=headers)

        # Assert: Should return error
        assert response.status_code >= 400

    def test_login_with_empty_json(self, client: FlaskClient):
        """Test login failure with empty request body."""
        # Arrange: Empty request data
        headers = make_api_headers()

        # Act: Make login request
        response = client.post("/api/v1/auth/login", json={}, headers=headers)

        # Assert: Should return error
        assert response.status_code >= 400


@pytest.mark.api
@pytest.mark.auth
class TestRegisterAPI:
    """Test /api/v1/auth/register endpoint."""

    def test_register_with_valid_data(
        self,
        client: FlaskClient,
        clean_db: Generator[Session, None, None],
    ):
        """Test successful registration with valid data."""
        # Arrange: Prepare valid registration data
        registration_data = make_registration_data(
            username="newuser",
            email="new@example.com",
            password="newpassword123",
        )
        headers = make_api_headers()

        # Act: Make registration request
        response = client.post(
            "/api/v1/auth/register",
            json=registration_data,
            headers=headers,
        )

        # Assert: Should return 201 created with token and user data
        data = assert_success_response(response, expected_status=201)
        assert "token" in data
        assert "refresh_token" in data
        assert "user" in data
        assert data["user"]["email"] == "new@example.com"
        assert data["user"]["username"] == "newuser"

    def test_register_with_duplicate_email(
        self, client: FlaskClient, clean_db: Generator[Session, None, None]
    ):
        """Test registration failure with existing email."""
        # Arrange: Create existing user and prepare data with same email
        existing_email = "existing@example.com"
        make_and_save_user(clean_db, email=existing_email)

        registration_data = make_registration_data(email=existing_email)
        headers = make_api_headers()

        # Act: Make registration request
        response = client.post(
            "/api/v1/auth/register",
            json=registration_data,
            headers=headers,
        )

        # Assert: Should return 400 bad request
        assert_error_response(response, expected_status=400)

    def test_register_with_password_mismatch(
        self,
        client: FlaskClient,
        clean_db: Generator[Session, None, None],
    ):
        """Test registration failure when passwords don't match."""
        # Arrange: Prepare data with mismatched passwords
        registration_data = make_registration_data()
        registration_data["confirm_password"] = "differentpassword"
        headers = make_api_headers()

        # Act: Make registration request
        response = client.post(
            "/api/v1/auth/register", json=registration_data, headers=headers
        )

        # Assert: Should return 400 bad request
        assert_error_response(response, expected_status=400)

    @pytest.mark.parametrize("missing_field", ["username", "email", "password"])
    def test_register_with_missing_fields(
        self,
        client: FlaskClient,
        clean_db: Generator[Session, None, None],
        missing_field: str,
    ):
        """Test registration failure when required fields are missing."""
        # Arrange: Prepare data with missing field
        registration_data = make_registration_data()
        del registration_data[missing_field]
        headers = make_api_headers()

        # Act: Make registration request
        response = client.post(
            "/api/v1/auth/register",
            json=registration_data,
            headers=headers,
        )

        # Assert: Should return error (400 or 500 depending on validation)
        assert response.status_code >= 400


@pytest.mark.api
@pytest.mark.auth
class TestRefreshTokenAPI:
    """Test /api/v1/auth/refresh endpoint."""

    def test_refresh_with_valid_token(
        self,
        client: FlaskClient,
        authenticated_user_with_tokens: dict[str, str | dict],
    ):
        """Test successful token refresh with valid refresh token."""
        # Arrange: Get refresh token from authenticated user
        refresh_token = authenticated_user_with_tokens["refresh_token"]
        headers = {"Authorization": f"Bearer {refresh_token}"}

        # Act: Make refresh request
        response = client.post("/api/v1/auth/refresh", headers=headers)

        # Assert: Should return new tokens
        data = assert_success_response(response, expected_status=200)
        assert "data" in data
        assert "access_token" in data["data"]
        assert "refresh_token" in data["data"]

    def test_refresh_without_token(self, client: FlaskClient):
        """Test refresh failure when no token provided."""
        # Act: Make refresh request without token
        response = client.post("/api/v1/auth/refresh")

        # Assert: Should return 401 unauthorized
        assert_error_response(response, expected_status=401)

    def test_refresh_with_access_token(
        self,
        client: FlaskClient,
        authenticated_user_with_tokens: dict[str, str | dict],
    ):
        """Test refresh failure when using access token instead of refresh token."""
        # Arrange: Use access token instead of refresh token
        access_token = authenticated_user_with_tokens["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}

        # Act: Make refresh request
        response = client.post("/api/v1/auth/refresh", headers=headers)

        # Assert: Should return 401 error (access token not valid for refresh)
        assert_error_response(response, expected_status=401)

    def test_refresh_with_invalid_token(self, client: FlaskClient):
        """Test refresh failure with invalid token."""
        # Arrange: Use invalid token
        headers = {"Authorization": "Bearer invalid.token.here"}

        # Act: Make refresh request
        response = client.post("/api/v1/auth/refresh", headers=headers)

        # Assert: Should return 401 unauthorized
        assert_error_response(response, expected_status=401)

    def test_refresh_with_expired_token(
        self,
        client: FlaskClient,
        clean_db: Generator[Session, None, None],
    ):
        """Test refresh failure with expired refresh token."""
        # Arrange: Create user and get tokens via API, then wait for expiration
        # Note: This test is challenging because we need an expired refresh token
        # For now, we'll test with a manually created expired token
        user = make_and_save_user(clean_db)

        # Create a token that's already expired using the same format as the API
        from datetime import timedelta

        from flask_jwt_extended import create_refresh_token

        with client.application.app_context():
            expired_token = create_refresh_token(
                identity=str(user.user_id),
                expires_delta=timedelta(seconds=-1),  # Expired 1 second ago
            )

        headers = {"Authorization": f"Bearer {expired_token}"}

        # Act: Make refresh request
        response = client.post("/api/v1/auth/refresh", headers=headers)

        # Assert: Should return 401 with token expired message
        assert_error_response(
            response,
            expected_status=401,
            expected_message=ErrorMessages.TOKEN_EXPIRED,
        )


@pytest.mark.api
@pytest.mark.auth
class TestAuthenticationFlow:
    """Test complete authentication flows."""

    def test_complete_login_flow(
        self,
        client: FlaskClient,
        clean_db: Generator[Session, None, None],
    ):
        """Test complete flow: register user, login, use token."""
        # Step 1: Register new user
        registration_data = make_registration_data(
            username="flowuser",
            email="flow@example.com",
            password="flowpassword123",
        )

        register_response = client.post(
            "/api/v1/auth/register",
            json=registration_data,
            headers=make_api_headers(),
        )
        register_data = assert_success_response(register_response, expected_status=201)

        # Step 2: Login with registered credentials
        login_data = make_login_data(
            email="flow@example.com",
            password="flowpassword123",
        )

        login_response = client.post(
            "/api/v1/auth/login",
            json=login_data,
            headers=make_api_headers(),
        )
        login_data = assert_success_response(login_response, expected_status=200)

        # Step 3: Verify tokens are different but both valid
        assert register_data["token"] != login_data["token"]  # Different tokens
        assert "token" in login_data
        assert "refresh_token" in login_data

        # Step 4: Use refresh token to get new access token
        refresh_headers = {"Authorization": f"Bearer {login_data['refresh_token']}"}
        refresh_response = client.post("/api/v1/auth/refresh", headers=refresh_headers)
        refresh_data = assert_success_response(refresh_response, expected_status=200)

        assert "access_token" in refresh_data["data"]
        assert "refresh_token" in refresh_data["data"]

    def test_authentication_with_invalid_credentials_flow(
        self,
        client: FlaskClient,
        clean_db: Generator[Session, None, None],
    ):
        """Test flow with invalid credentials at various steps."""
        # Step 1: Register user
        registration_data = make_registration_data(
            username="invalidflow",
            email="invalid@example.com",
            password="validpassword123",
        )

        register_response = client.post(
            "/api/v1/auth/register",
            json=registration_data,
            headers=make_api_headers(),
        )
        assert_success_response(register_response, expected_status=201)

        # Step 2: Try login with wrong password
        wrong_login_data = make_login_data(
            email="invalid@example.com",
            password="wrongpassword",
        )

        login_response = client.post(
            "/api/v1/auth/login",
            json=wrong_login_data,
            headers=make_api_headers(),
        )
        assert_error_response(
            login_response,
            expected_status=401,
            expected_message=ErrorMessages.INVALID_CREDENTIALS,
        )

        # Step 3: Try login with correct credentials (should work)
        correct_login_data = make_login_data(
            email="invalid@example.com",
            password="validpassword123",
        )

        login_response = client.post(
            "/api/v1/auth/login",
            json=correct_login_data,
            headers=make_api_headers(),
        )
        login_data = assert_success_response(login_response, expected_status=200)

        # Step 4: Verify we can use the token
        refresh_headers = {"Authorization": f"Bearer {login_data['refresh_token']}"}
        refresh_response = client.post("/api/v1/auth/refresh", headers=refresh_headers)
        assert_success_response(refresh_response, expected_status=200)


@pytest.mark.api
@pytest.mark.auth
class TestAuthTokenValidation:
    """Test authentication token validation scenarios."""

    def test_access_with_expired_token(
        self,
        client: FlaskClient,
        clean_db: Generator[Session, None, None],
    ):
        """Test that expired token returns appropriate error."""
        # Arrange: Create user and expired token
        user = make_and_save_user(clean_db)

        # Create expired token with proper app context
        from datetime import timedelta

        from flask_jwt_extended import create_refresh_token

        with client.application.app_context():
            expired_token = create_refresh_token(
                identity=str(user.user_id),
                expires_delta=timedelta(seconds=-1),  # Expired 1 second ago
            )

        headers = {"Authorization": f"Bearer {expired_token}"}

        # Act: Try to use expired token (using refresh endpoint as example)
        response = client.post("/api/v1/auth/refresh", headers=headers)

        # Assert: Should return 401 with token expired message
        assert_error_response(
            response,
            expected_status=401,
            expected_message=ErrorMessages.TOKEN_EXPIRED,
        )

    def test_access_with_malformed_token(self, client: FlaskClient):
        """Test that malformed token returns appropriate error."""
        # Arrange: Create malformed token
        headers = {"Authorization": "Bearer malformed.token"}

        # Act: Try to use malformed token
        response = client.post("/api/v1/auth/refresh", headers=headers)

        # Assert: Should return 401 unauthorized
        assert_error_response(response, expected_status=401)

    def test_access_without_token(self, client: FlaskClient):
        """Test that missing token returns appropriate error."""
        # Act: Try to access protected endpoint without token
        response = client.post("/api/v1/auth/refresh")

        # Assert: Should return 401 unauthorized
        assert_error_response(
            response,
            expected_status=401,
            expected_message=ErrorMessages.UNAUTHORIZED,
        )

    def test_access_with_invalid_bearer_format(self, client: FlaskClient):
        """Test that invalid bearer format returns appropriate error."""
        # Arrange: Create invalid authorization header format
        headers = {"Authorization": "InvalidFormat token"}

        # Act: Try to use invalid format
        response = client.post("/api/v1/auth/refresh", headers=headers)

        # Assert: Should return 401 unauthorized
        assert_error_response(response, expected_status=401)


@pytest.mark.api
@pytest.mark.auth
class TestAuthDataValidation:
    """Test validation of authentication request data."""

    @pytest.mark.parametrize(
        ("invalid_email", "expected_status"),
        [
            ("", 401),  # Empty email - treated as authentication failure
            (
                "invalid-email",
                401,
            ),  # Invalid format - treated as authentication failure
            (
                "@example.com",
                401,
            ),  # Missing local part - treated as authentication failure
            ("user@", 401),  # Missing domain - treated as authentication failure
        ],
    )
    def test_login_with_invalid_email_formats(
        self,
        client: FlaskClient,
        clean_db: Generator[Session, None, None],
        invalid_email: str,
        expected_status: int,
    ):
        """
        Test login with various invalid email formats.

        Note: Invalid email formats are treated as authentication failures (401)
        rather than validation errors (400) for security reasons.
        """
        # Arrange: Prepare login data with invalid email
        login_data = make_login_data(email=invalid_email, password="password123")
        headers = make_api_headers()

        # Act: Make login request
        response = client.post("/api/v1/auth/login", json=login_data, headers=headers)

        # Assert: Should return authentication failure
        assert_error_response(
            response,
            expected_status=expected_status,
            expected_message=ErrorMessages.INVALID_CREDENTIALS,
        )

    @pytest.mark.parametrize(
        ("invalid_password", "expected_status"),
        [
            ("", 400),  # Empty password
            ("123", 400),  # Too short
        ],
    )
    def test_register_with_invalid_password_formats(
        self,
        client: FlaskClient,
        clean_db: Generator[Session, None, None],
        invalid_password: str,
        expected_status: int,
    ):
        """Test registration validation with various invalid password formats."""
        # Arrange: Prepare registration data with invalid password
        registration_data = make_registration_data(password=invalid_password)
        registration_data["confirm_password"] = invalid_password
        headers = make_api_headers()

        # Act: Make registration request
        response = client.post(
            "/api/v1/auth/register",
            json=registration_data,
            headers=headers,
        )

        # Assert: Should return appropriate error status
        assert response.status_code >= expected_status
