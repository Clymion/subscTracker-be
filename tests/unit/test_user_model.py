"""
Unit tests for User model.

Pure unit tests that do not depend on database connections, environment variables,
or external configurations. Tests focus on model logic, validation, and behavior.
"""

from datetime import datetime, timezone

from app.models.user import User


class TestUserModelCreation:
    """Test User model creation and basic attributes."""

    def test_user_creation_with_all_fields(self):
        """Test creating a user with all required fields."""
        # Arrange
        user_id = 1
        username = "testuser"
        email = "test@example.com"
        created_time = datetime.now(tz=timezone.utc)
        updated_time = datetime.now(tz=timezone.utc)

        # Act
        user = User(
            user_id=user_id,
            username=username,
            email=email,
            created_at=created_time,
            updated_at=updated_time,
        )

        # Assert
        assert user.user_id == user_id
        assert user.username == username
        assert user.email == email
        assert user.created_at == created_time
        assert user.updated_at == updated_time

    def test_user_creation_with_minimal_fields(self):
        """Test creating a user with minimal required fields."""
        # Arrange & Act
        user = User(username="minimaluser", email="minimal@example.com")

        # Assert
        assert user.username == "minimaluser"
        assert user.email == "minimal@example.com"
        # created_at and updated_at should be set by SQLAlchemy defaults when saved
        # but for pure unit test, we don't test database behavior

    def test_user_attributes_are_correctly_assigned(self):
        """Test that all user attributes are correctly assigned."""
        # Arrange
        test_data = {
            "user_id": 42,
            "username": "attributetest",
            "email": "attribute@test.com",
            "created_at": datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            "updated_at": datetime(2024, 1, 2, 12, 0, 0, tzinfo=timezone.utc),
        }

        # Act
        user = User(**test_data)

        # Assert
        for key, expected_value in test_data.items():
            assert getattr(user, key) == expected_value


class TestUserPasswordManagement:
    """Test User model password hashing and verification."""

    def test_set_password_creates_hash(self):
        """Test that setting a password creates a password hash."""
        # Arrange
        user = User(username="hashtest", email="hash@test.com")
        password = "mysecretpassword"

        # Act
        user.set_password(password)

        # Assert
        assert hasattr(user, "password_hash")
        assert user.password_hash is not None
        assert user.password_hash != password  # Should be hashed, not plain text
        assert len(user.password_hash) > len(password)  # Hash should be longer

    def test_check_password_with_correct_password(self):
        """Test password verification with correct password."""
        # Arrange
        user = User(username="correcttest", email="correct@test.com")
        password = "correctpassword123"
        user.set_password(password)

        # Act & Assert
        assert user.check_password(password) is True

    def test_check_password_with_incorrect_password(self):
        """Test password verification with incorrect password."""
        # Arrange
        user = User(username="incorrecttest", email="incorrect@test.com")
        correct_password = "correctpassword123"
        wrong_password = "wrongpassword456"
        user.set_password(correct_password)

        # Act & Assert
        assert user.check_password(wrong_password) is False

    def test_check_password_with_empty_password(self):
        """Test password verification with empty password."""
        # Arrange
        user = User(username="emptytest", email="empty@test.com")
        user.set_password("nonemptypassword")

        # Act & Assert
        assert user.check_password("") is False

    def test_password_hash_changes_with_different_passwords(self):
        """Test that different passwords create different hashes."""
        # Arrange
        user = User(username="hashchange", email="hashchange@test.com")
        password1 = "password123"
        password2 = "differentpassword456"

        # Act
        user.set_password(password1)
        hash1 = user.password_hash

        user.set_password(password2)
        hash2 = user.password_hash

        # Assert
        assert hash1 != hash2
        assert user.check_password(password2) is True
        assert user.check_password(password1) is False

    def test_same_password_creates_different_hashes(self):
        """Test that the same password creates different hashes (due to salt)."""
        # Arrange
        user1 = User(username="salt1", email="salt1@test.com")
        user2 = User(username="salt2", email="salt2@test.com")
        same_password = "samepassword123"

        # Act
        user1.set_password(same_password)
        user2.set_password(same_password)

        # Assert
        assert user1.password_hash != user2.password_hash  # Different due to salt
        assert user1.check_password(same_password) is True
        assert user2.check_password(same_password) is True


class TestUserStringRepresentation:
    """Test User model string representation."""

    def test_user_str_representation(self):
        """Test that user string representation returns correct format."""
        # Arrange
        username = "stringtestuser"
        user = User(username=username, email="stringtest@example.com")

        # Act
        result = str(user)

        # Assert
        expected = f"<User {username}>"
        assert result == expected

    def test_user_repr_representation(self):
        """Test that user repr representation returns correct format."""
        # Arrange
        username = "reprtestuser"
        user = User(username=username, email="reprtest@example.com")

        # Act
        result = repr(user)

        # Assert
        expected = f"<User {username}>"
        assert result == expected

    def test_str_representation_with_special_characters(self):
        """Test string representation with special characters in username."""
        # Arrange
        username = "user_with-special.chars"
        user = User(username=username, email="special@example.com")

        # Act
        result = str(user)

        # Assert
        expected = f"<User {username}>"
        assert result == expected


class TestUserModelEdgeCases:
    """Test User model edge cases and boundary conditions."""

    def test_user_with_long_username(self):
        """Test user creation with maximum length username."""
        # Arrange
        # Assuming max length is 32 characters based on model definition
        long_username = "a" * 32
        user = User(username=long_username, email="longusername@test.com")

        # Act & Assert
        assert user.username == long_username
        assert len(user.username) == 32

    def test_user_with_long_email(self):
        """Test user creation with long email address."""
        # Arrange
        # Create a long but valid email (under 255 chars limit)
        long_email = "verylongemailaddress" + "x" * 200 + "@example.com"
        user = User(username="longemail", email=long_email)

        # Act & Assert
        assert user.email == long_email

    def test_password_with_special_characters(self):
        """Test password handling with special characters."""
        # Arrange
        user = User(username="specialpass", email="special@test.com")
        special_password = "!@#$%^&*()_+-=[]{}|;:,.<>?"

        # Act
        user.set_password(special_password)

        # Assert
        assert user.check_password(special_password) is True
        assert user.check_password("wrongpassword") is False

    def test_password_with_unicode_characters(self):
        """Test password handling with unicode characters."""
        # Arrange
        user = User(username="unicode", email="unicode@test.com")
        unicode_password = "パスワード123测试🔒"

        # Act
        user.set_password(unicode_password)

        # Assert
        assert user.check_password(unicode_password) is True
        assert user.check_password("wrongpassword") is False

    def test_multiple_password_changes(self):
        """Test changing password multiple times."""
        # Arrange
        user = User(username="multichange", email="multi@test.com")
        passwords = ["password1", "password2", "password3", "finalpassword"]

        # Act & Assert
        for i, password in enumerate(passwords):
            user.set_password(password)

            # Current password should work
            assert user.check_password(password) is True

            # Previous passwords should not work
            for prev_password in passwords[:i]:
                assert user.check_password(prev_password) is False


class TestUserModelTypes:
    """Test User model type handling and validation."""

    def test_user_id_is_integer(self):
        """Test that user_id is properly handled as integer."""
        # Arrange & Act
        user = User(user_id=123, username="inttest", email="int@test.com")

        # Assert
        assert isinstance(user.user_id, int)
        assert user.user_id == 123

    def test_username_is_string(self):
        """Test that username is properly handled as string."""
        # Arrange & Act
        user = User(username="stringtest", email="string@test.com")

        # Assert
        assert isinstance(user.username, str)
        assert user.username == "stringtest"

    def test_email_is_string(self):
        """Test that email is properly handled as string."""
        # Arrange & Act
        user = User(username="emailtest", email="email@test.com")

        # Assert
        assert isinstance(user.email, str)
        assert user.email == "email@test.com"

    def test_datetime_fields_are_datetime_objects(self):
        """Test that datetime fields are properly handled as datetime objects."""
        # Arrange
        now = datetime.now(timezone.utc)
        user = User(
            username="datetimetest",
            email="datetime@test.com",
            created_at=now,
            updated_at=now,
        )

        # Act & Assert
        assert isinstance(user.created_at, datetime)
        assert isinstance(user.updated_at, datetime)
        assert user.created_at == now
        assert user.updated_at == now
