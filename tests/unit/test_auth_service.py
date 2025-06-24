"""
Unit tests for AuthService with Full Config pattern.

Full Config pattern tests that use TestConfig and database sessions.
These tests cover AuthService business logic with real database operations.
"""

from collections.abc import Generator

import pytest
from sqlalchemy.orm import Session

from app.constants import ErrorMessages
from app.services.auth_service import AuthService
from tests.helpers import make_and_save_user, make_registration_data


@pytest.mark.unit
@pytest.mark.auth
class TestAuthServiceSetup:
    """Base setup for AuthService tests with full configuration."""

    @pytest.fixture
    def auth_service(self) -> AuthService:
        """
        Create AuthService instance for testing.

        Returns:
            AuthService: Service instance ready for testing.
        """
        return AuthService()


@pytest.mark.unit
@pytest.mark.auth
class TestAuthServiceAuthenticate(TestAuthServiceSetup):
    """Test AuthService.authenticate method with full configuration."""

    def test_authenticate_with_valid_credentials_returns_user(
        self,
        auth_service: AuthService,
        clean_db: Generator[Session, None, None],
    ) -> None:
        """Test successful authentication with correct email and password."""
        # Arrange: Create a user with known credentials
        user = make_and_save_user(
            clean_db,
            email="valid@example.com",
            password="correctpassword",
            username="validuser",
        )

        # Act: Attempt to authenticate
        result = auth_service.authenticate("valid@example.com", "correctpassword")

        # Assert: Authentication should succeed and return correct user
        assert result is not None
        assert result.email == "valid@example.com"
        assert result.username == "validuser"
        assert result.user_id == user.user_id
        assert result.check_password("correctpassword")

    def test_authenticate_with_nonexistent_email_returns_none(
        self,
        auth_service: AuthService,
        clean_db: Generator[Session, None, None],
    ) -> None:
        """Test authentication failure with non-existent email."""
        # Arrange: Create a user but try different email
        make_and_save_user(clean_db, email="real@example.com")

        # Act: Try to authenticate with wrong email
        result = auth_service.authenticate("wrong@example.com", "anypassword")

        # Assert: Authentication should fail
        assert result is None

    def test_authenticate_with_incorrect_password_returns_none(
        self,
        auth_service: AuthService,
        clean_db: Generator[Session, None, None],
    ) -> None:
        """Test authentication failure with incorrect password."""
        # Arrange: Create a user with known password
        make_and_save_user(
            clean_db,
            email="user@example.com",
            password="correctpassword",
        )

        # Act: Try to authenticate with wrong password
        result = auth_service.authenticate("user@example.com", "wrongpassword")

        # Assert: Authentication should fail
        assert result is None

    def test_authenticate_with_empty_database_returns_none(
        self,
        auth_service: AuthService,
        clean_db: Generator[Session, None, None],
    ) -> None:
        """Test authentication when no users exist in database."""
        # Arrange: Empty database (clean_db ensures this)

        # Act: Try to authenticate
        result = auth_service.authenticate("any@example.com", "anypassword")

        # Assert: Authentication should fail
        assert result is None

    def test_authenticate_with_case_sensitive_email(
        self,
        auth_service: AuthService,
        clean_db: Generator[Session, None, None],
    ) -> None:
        """Test authentication with case sensitivity in email."""
        # Arrange: Create user with lowercase email
        make_and_save_user(
            clean_db,
            email="test@example.com",
            password="testpassword",
        )

        # Act: Try to authenticate with different case
        result = auth_service.authenticate("TEST@EXAMPLE.COM", "testpassword")

        # Assert: Should fail (assuming case-sensitive email lookup)
        assert result is None

    @pytest.mark.parametrize(
        ("email", "password", "should_succeed"),
        [
            ("valid@example.com", "correctpassword", True),
            ("valid@example.com", "wrongpassword", False),
            ("invalid@example.com", "correctpassword", False),
            ("invalid@example.com", "wrongpassword", False),
        ],
    )
    def test_authenticate_with_various_credentials(
        self,
        auth_service: AuthService,
        clean_db: Generator[Session, None, None],
        email: str,
        password: str,
        should_succeed: bool,
    ) -> None:
        """Test authentication with various credential combinations."""
        # Arrange: Create user with known credentials
        make_and_save_user(
            clean_db,
            email="valid@example.com",
            password="correctpassword",
        )

        # Act: Try to authenticate
        result = auth_service.authenticate(email, password)

        # Assert: Result should match expectation
        if should_succeed:
            assert result is not None
            assert result.email == email
        else:
            assert result is None


@pytest.mark.unit
@pytest.mark.auth
class TestAuthServiceRegisterUser(TestAuthServiceSetup):
    """Test AuthService.register_user method with full configuration."""

    def test_register_user_with_valid_data_creates_user(
        self,
        auth_service: AuthService,
        clean_db: Generator[Session, None, None],
    ) -> None:
        """Test successful user registration with valid data."""
        # Arrange: Prepare valid registration data
        registration_data = make_registration_data(
            username="newuser",
            email="new@example.com",
            password="newpassword123",
        )

        # Act: Register the user
        result = auth_service.register_user(registration_data)

        # Assert: User should be created successfully
        assert result is not None
        assert result.username == "newuser"
        assert result.email == "new@example.com"
        assert result.check_password("newpassword123")
        assert result.user_id is not None  # Should have an ID after saving

        # Assert: User should be persisted in database
        from app.models.user import User

        saved_user = clean_db.query(User).filter_by(email="new@example.com").first()
        assert saved_user is not None
        assert saved_user.user_id == result.user_id

    def test_register_user_with_duplicate_email_raises_error(
        self,
        auth_service: AuthService,
        clean_db: Generator[Session, None, None],
    ) -> None:
        """Test registration failure when email already exists."""
        # Arrange: Create existing user and prepare data with same email
        existing_email = "existing@example.com"
        make_and_save_user(clean_db, email=existing_email)

        registration_data = make_registration_data(email=existing_email)

        # Act & Assert: Registration should fail with appropriate error
        with pytest.raises(ValueError, match=ErrorMessages.DUPLICATE_EMAIL):
            auth_service.register_user(registration_data)

    def test_register_user_with_duplicate_username_raises_error(
        self,
        auth_service: AuthService,
        clean_db: Generator[Session, None, None],
    ) -> None:
        """Test registration failure when username already exists."""
        # Arrange: Create existing user and prepare data with same username
        existing_username = "existinguser"
        make_and_save_user(clean_db, username=existing_username)

        registration_data = make_registration_data(
            username=existing_username,
            email="different@example.com",
        )

        # Act & Assert: Registration should fail with appropriate error
        with pytest.raises(ValueError, match=ErrorMessages.DUPLICATE_USERNAME):
            auth_service.register_user(registration_data)

    def test_register_user_with_password_mismatch_raises_error(
        self,
        auth_service: AuthService,
        clean_db: Generator[Session, None, None],
    ) -> None:
        """Test registration failure when passwords don't match."""
        # Arrange: Prepare data with mismatched passwords
        registration_data = make_registration_data()
        registration_data["confirm_password"] = "differentpassword"

        # Act & Assert: Registration should fail with specific error message
        with pytest.raises(ValueError, match="Passwords do not match"):
            auth_service.register_user(registration_data)

    @pytest.mark.parametrize("missing_field", ["username", "email", "password"])
    def test_register_user_with_missing_required_fields_raises_error(
        self,
        auth_service: AuthService,
        clean_db: Generator[Session, None, None],
        missing_field: str,
    ) -> None:
        """Test registration failure when required fields are missing."""
        # Arrange: Prepare data with missing field
        registration_data = make_registration_data()
        del registration_data[missing_field]

        # Act & Assert: Registration should fail
        with pytest.raises((ValueError, TypeError, AttributeError)):
            auth_service.register_user(registration_data)

    @pytest.mark.parametrize(
        ("field", "invalid_value"),
        [
            ("username", ""),
            ("email", ""),
            ("password", ""),
            ("email", "invalid-email"),
            ("username", " "),  # Whitespace only
        ],
    )
    def test_register_user_with_invalid_field_values_raises_error(
        self,
        auth_service: AuthService,
        clean_db: Generator[Session, None, None],
        field: str,
        invalid_value: str,
    ) -> None:
        """Test registration failure with invalid field values."""
        # Arrange: Prepare data with invalid field value
        registration_data = make_registration_data()
        registration_data[field] = invalid_value

        # Act & Assert: Registration should fail
        with pytest.raises(ValueError):
            auth_service.register_user(registration_data)

    def test_register_user_preserves_password_security(
        self,
        auth_service: AuthService,
        clean_db: Generator[Session, None, None],
    ) -> None:
        """Test that registration properly hashes passwords."""
        # Arrange: Prepare registration data
        plain_password = "secretpassword123"
        registration_data = make_registration_data(password=plain_password)

        # Act: Register the user
        result = auth_service.register_user(registration_data)

        # Assert: Password should be hashed, not stored in plain text
        assert result.password_hash != plain_password
        assert len(result.password_hash) > len(plain_password)
        assert result.check_password(plain_password)
        assert not result.check_password("wrongpassword")


@pytest.mark.unit
@pytest.mark.auth
class TestAuthServiceIntegration(TestAuthServiceSetup):
    """Integration tests for AuthService methods working together."""

    def test_complete_registration_and_authentication_flow(
        self,
        auth_service: AuthService,
        clean_db: Generator[Session, None, None],
    ) -> None:
        """Test complete flow: register user then authenticate."""
        # Arrange: Prepare registration data
        registration_data = make_registration_data(
            username="flowuser",
            email="flow@example.com",
            password="flowpassword123",
        )

        # Act: Register user
        registered_user = auth_service.register_user(registration_data)

        # Act: Authenticate the same user
        authenticated_user = auth_service.authenticate(
            "flow@example.com",
            "flowpassword123",
        )

        # Assert: Both operations should succeed and return same user
        assert registered_user is not None
        assert authenticated_user is not None
        assert registered_user.user_id == authenticated_user.user_id
        assert registered_user.email == authenticated_user.email
        assert registered_user.username == authenticated_user.username

    def test_register_multiple_users_with_unique_credentials(
        self,
        auth_service: AuthService,
        clean_db: Generator[Session, None, None],
    ) -> None:
        """Test registering multiple users with different credentials."""
        # Arrange: Prepare multiple registration datasets
        users_data = [
            make_registration_data(username="user1", email="user1@example.com"),
            make_registration_data(username="user2", email="user2@example.com"),
            make_registration_data(username="user3", email="user3@example.com"),
        ]

        # Act: Register all users
        created_users = []
        for data in users_data:
            user = auth_service.register_user(data)
            created_users.append(user)

        # Assert: All users should be created with unique IDs
        assert len(created_users) == 3
        user_ids = [user.user_id for user in created_users]
        assert len(set(user_ids)) == 3  # All IDs should be unique

        # Assert: Each user can authenticate independently
        for i, user_data in enumerate(users_data):
            auth_result = auth_service.authenticate(
                user_data["email"],
                user_data["password"],
            )
            assert auth_result is not None
            assert auth_result.user_id == created_users[i].user_id
            assert auth_result.username == user_data["username"]

    def test_authentication_after_failed_registration_attempts(
        self,
        auth_service: AuthService,
        clean_db: Generator[Session, None, None],
    ) -> None:
        """Test authentication works after failed registration attempts."""
        # Arrange: First, create a valid user
        valid_data = make_registration_data(
            username="validuser",
            email="valid@example.com",
            password="validpassword123",
        )
        auth_service.register_user(valid_data)

        # Act: Try to register with duplicate email (should fail)
        duplicate_data = make_registration_data(email="valid@example.com")
        with pytest.raises(ValueError):
            auth_service.register_user(duplicate_data)

        # Act: Try to register with password mismatch (should fail)
        mismatch_data = make_registration_data()
        mismatch_data["confirm_password"] = "different"
        with pytest.raises(ValueError):
            auth_service.register_user(mismatch_data)

        # Act: Authenticate the originally valid user
        auth_result = auth_service.authenticate(
            "valid@example.com",
            "validpassword123",
        )

        # Assert: Authentication should still work
        assert auth_result is not None
        assert auth_result.email == "valid@example.com"
        assert auth_result.username == "validuser"

    def test_concurrent_user_operations_with_database_integrity(
        self,
        auth_service: AuthService,
        clean_db: Generator[Session, None, None],
    ) -> None:
        """Test that user operations maintain database integrity."""
        # Arrange: Prepare test data
        base_email = "integrity@example.com"
        password = "testpassword123"

        # Act: Register user
        registration_data = make_registration_data(
            email=base_email,
            password=password,
        )
        registered_user = auth_service.register_user(registration_data)

        # Act: Authenticate multiple times
        auth_results = []
        for _ in range(3):
            result = auth_service.authenticate(base_email, password)
            auth_results.append(result)

        # Assert: All authentication results should be consistent
        for result in auth_results:
            assert result is not None
            assert result.user_id == registered_user.user_id
            assert result.email == base_email

        # Assert: Database should contain exactly one user with this email
        from app.models.user import User

        users_with_email = clean_db.query(User).filter_by(email=base_email).all()
        assert len(users_with_email) == 1
        assert users_with_email[0].user_id == registered_user.user_id


@pytest.mark.unit
@pytest.mark.auth
class TestAuthServiceErrorHandling(TestAuthServiceSetup):
    """Test AuthService error handling and edge cases."""

    def test_register_user_with_none_values_raises_appropriate_errors(
        self,
        auth_service: AuthService,
        clean_db: Generator[Session, None, None],
    ) -> None:
        """Test registration behavior with None values."""
        # Arrange: Prepare data with None values
        invalid_data_sets = [
            {**make_registration_data(), "username": None},
            {**make_registration_data(), "email": None},
            {**make_registration_data(), "password": None},
        ]

        for invalid_data in invalid_data_sets:
            # Act & Assert: Should raise appropriate error
            with pytest.raises((ValueError, TypeError, AttributeError)):
                auth_service.register_user(invalid_data)

    def test_authenticate_with_none_values_returns_none(
        self,
        auth_service: AuthService,
        clean_db: Generator[Session, None, None],
    ) -> None:
        """Test authentication behavior with None values."""
        # Act & Assert: Should handle None gracefully
        assert auth_service.authenticate(None, "password") is None
        assert auth_service.authenticate("email@example.com", None) is None
        assert auth_service.authenticate(None, None) is None

    def test_authenticate_with_special_characters_in_credentials(
        self,
        auth_service: AuthService,
        clean_db: Generator[Session, None, None],
    ) -> None:
        """Test authentication with special characters in credentials."""
        # Arrange: Create user with special characters
        special_email = "user+special@example.com"
        special_password = "p@ssw0rd!#$%^&*()"

        make_and_save_user(
            clean_db,
            email=special_email,
            password=special_password,
        )

        # Act: Authenticate with special characters
        result = auth_service.authenticate(special_email, special_password)

        # Assert: Should work correctly
        assert result is not None
        assert result.email == special_email

    def test_register_user_handles_database_transaction_properly(
        self,
        auth_service: AuthService,
        clean_db: Generator[Session, None, None],
    ) -> None:
        """Test that registration handles database transactions properly."""
        # Arrange: Create a user first
        first_user_data = make_registration_data(
            username="firstuser",
            email="first@example.com",
        )
        auth_service.register_user(first_user_data)

        # Act: Try to register with duplicate email (should trigger rollback)
        duplicate_data = make_registration_data(
            username="seconduser",
            email="first@example.com",  # Duplicate email
        )

        # Assert: Should raise error and not affect database state
        with pytest.raises(ValueError):
            auth_service.register_user(duplicate_data)

        # Assert: Original user should still exist and be authenticatable
        auth_result = auth_service.authenticate(
            "first@example.com",
            first_user_data["password"],
        )
        assert auth_result is not None
        assert auth_result.username == "firstuser"

        # Assert: Second user should not exist in database
        from app.models.user import User

        users_named_second = clean_db.query(User).filter_by(username="seconduser").all()
        assert len(users_named_second) == 0
