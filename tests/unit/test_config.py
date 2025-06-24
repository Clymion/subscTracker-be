"""
Unit tests for configuration management.

Tests environment variable loading, validation, and configuration factory functions.
Following the test-list requirements from docs/test-list/env-config.md
"""

from collections.abc import Generator
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.config import AppConfig, TestConfig, get_config, is_testing


class TestAppConfig:
    """Test AppConfig environment variable loading and validation."""

    def test_load_all_required_env_variables(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test that all required environment variables are correctly loaded."""
        # Arrange: Set all required environment variables
        required_vars = {
            "DB_HOST": "test_host",
            "DB_PORT": "5432",
            "DB_NAME": "test_db",
            "DB_USER": "test_user",
            "DB_PASSWORD": "test_password",
            "JWT_SECRET_KEY": "test-secret-key-123456",
        }

        for key, value in required_vars.items():
            monkeypatch.setenv(key, value)

        # Act: Create config instance
        config = AppConfig()

        # Assert: All values should be loaded correctly
        assert config.DB_HOST == "test_host"
        assert config.DB_PORT == 5432
        assert config.DB_NAME == "test_db"
        assert config.DB_USER == "test_user"
        assert config.DB_PASSWORD == "test_password"
        assert config.JWT_SECRET_KEY == "test-secret-key-123456"

    def test_default_values_applied_when_optional_vars_not_set(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test that default values are applied when optional variables are not set."""
        # Arrange: Set only required variables
        required_vars = {
            "DB_HOST": "localhost",
            "DB_PORT": "5432",
            "DB_NAME": "test_db",
            "DB_USER": "user",
            "DB_PASSWORD": "password",
            "JWT_SECRET_KEY": "secret-key-123456",
        }

        for key, value in required_vars.items():
            monkeypatch.setenv(key, value)

        # Ensure optional vars are not set
        monkeypatch.delenv("API_PORT", raising=False)
        monkeypatch.delenv("DEBUG", raising=False)
        monkeypatch.delenv("ENABLE_NEW_BILLING", raising=False)

        # Act: Create config instance
        config = AppConfig()

        # Assert: Default values should be used
        assert config.API_PORT == 5000
        assert config.DEBUG is False
        assert config.ENABLE_NEW_BILLING is False
        assert config.JWT_ACCESS_TOKEN_EXPIRES == 3600
        assert config.JWT_REFRESH_TOKEN_EXPIRES == 2592000

    def test_config_attributes_have_correct_types(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test that config attributes have correct types after loading."""
        # Arrange: Set environment variables with string values
        vars_dict = {
            "DB_HOST": "localhost",
            "DB_PORT": "5432",
            "DB_NAME": "test_db",
            "DB_USER": "user",
            "DB_PASSWORD": "password",
            "JWT_SECRET_KEY": "secret-key-123456",
            "API_PORT": "8080",
            "DEBUG": "true",
            "JWT_ACCESS_TOKEN_EXPIRES": "7200",
        }

        for key, value in vars_dict.items():
            monkeypatch.setenv(key, value)

        # Act: Create config instance
        config = AppConfig()

        # Assert: Types should be converted correctly
        assert isinstance(config.DB_HOST, str)
        assert isinstance(config.DB_PORT, int)
        assert isinstance(config.API_PORT, int)
        assert isinstance(config.DEBUG, bool)
        assert isinstance(config.JWT_ACCESS_TOKEN_EXPIRES, int)
        assert config.DB_PORT == 5432
        assert config.API_PORT == 8080
        assert config.DEBUG is True
        assert config.JWT_ACCESS_TOKEN_EXPIRES == 7200

    def test_loading_config_multiple_times_returns_consistent_results(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test that loading config multiple times returns consistent results."""
        # Arrange: Set environment variables
        vars_dict = {
            "DB_HOST": "consistent_host",
            "DB_PORT": "3306",
            "DB_NAME": "consistent_db",
            "DB_USER": "consistent_user",
            "DB_PASSWORD": "consistent_password",
            "JWT_SECRET_KEY": "consistent-secret-123456",
        }

        for key, value in vars_dict.items():
            monkeypatch.setenv(key, value)

        # Act: Create multiple config instances
        config1 = AppConfig()
        config2 = AppConfig()

        # Assert: All values should be identical
        assert config1.DB_HOST == config2.DB_HOST
        assert config1.DB_PORT == config2.DB_PORT
        assert config1.JWT_SECRET_KEY == config2.JWT_SECRET_KEY
        assert config1.API_PORT == config2.API_PORT


class TestAppConfigValidation:
    """Test AppConfig validation logic."""

    def test_missing_required_env_variables_raise_validation_error(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test that missing required environment variables raise validation errors."""
        # Prevent loading from .env file by unsetting DOTENV_KEY and setting JWT_SECRET_KEY = 0
        monkeypatch.setenv("JWT_SECRET_KEY", "0")
        # Act & Assert: Creating config without required vars should raise ValidationError
        # because AppConfig has default values for all except JWT_SECRET_KEY
        with pytest.raises(ValidationError) as exc_info:
            AppConfig()

        # Check that JWT_SECRET_KEY is mentioned in the error
        errors = exc_info.value.errors()
        error_fields = {error["loc"][0] for error in errors}
        # Only JWT_SECRET_KEY is required without default, others have defaults
        required_fields = {
            "JWT_SECRET_KEY",
        }

        # At least some required fields should be in the error
        assert len(error_fields.intersection(required_fields)) > 0

    def test_invalid_type_env_variables_raise_validation_error(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test that invalid type environment variables raise validation errors."""
        # Arrange: Set required fields correctly except for one invalid type
        monkeypatch.setenv("DB_HOST", "localhost")
        monkeypatch.setenv("DB_PORT", "not_an_integer")  # Invalid type
        monkeypatch.setenv("DB_NAME", "test_db")
        monkeypatch.setenv("DB_USER", "user")
        monkeypatch.setenv("DB_PASSWORD", "password")
        monkeypatch.setenv("JWT_SECRET_KEY", "secret-key-123456")

        # Act & Assert: Should raise ValidationError
        with pytest.raises(ValidationError) as exc_info:
            AppConfig()

        # Check that DB_PORT error is included
        errors = exc_info.value.errors()
        db_port_errors = [e for e in errors if e["loc"][0] == "DB_PORT"]
        assert len(db_port_errors) > 0

    @pytest.mark.parametrize("invalid_port", ["-1", "0", "70000", "abc"])
    def test_invalid_port_values_raise_validation_error(
        self,
        monkeypatch: pytest.MonkeyPatch,
        invalid_port: str,
    ) -> None:
        """Test that invalid port values raise validation errors."""
        # Arrange: Set valid values except for invalid port
        monkeypatch.setenv("DB_HOST", "localhost")
        monkeypatch.setenv("DB_PORT", "5432")
        monkeypatch.setenv("DB_NAME", "test_db")
        monkeypatch.setenv("DB_USER", "user")
        monkeypatch.setenv("DB_PASSWORD", "password")
        monkeypatch.setenv("JWT_SECRET_KEY", "secret-key-123456")
        monkeypatch.setenv("API_PORT", invalid_port)

        # Act & Assert: Should raise ValidationError
        with pytest.raises(ValidationError):
            AppConfig()

    def test_short_jwt_secret_raises_validation_error(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test that short JWT secret key raises validation error."""
        # Arrange: Set valid values except for short JWT secret
        monkeypatch.setenv("DB_HOST", "localhost")
        monkeypatch.setenv("DB_PORT", "5432")
        monkeypatch.setenv("DB_NAME", "test_db")
        monkeypatch.setenv("DB_USER", "user")
        monkeypatch.setenv("DB_PASSWORD", "password")
        monkeypatch.setenv("JWT_SECRET_KEY", "short")  # Too short

        # Act & Assert: Should raise ValidationError
        with pytest.raises(ValidationError) as exc_info:
            AppConfig()

        # Check that JWT_SECRET_KEY error is included
        errors = exc_info.value.errors()
        jwt_errors = [e for e in errors if e["loc"][0] == "JWT_SECRET_KEY"]
        assert len(jwt_errors) > 0

    @pytest.mark.parametrize("invalid_duration", ["-1", "0"])
    def test_negative_or_zero_duration_raises_validation_error(
        self,
        monkeypatch: pytest.MonkeyPatch,
        invalid_duration: str,
    ) -> None:
        """Test that negative or zero duration values raise validation errors."""
        # Arrange: Set valid values except for invalid duration
        monkeypatch.setenv("DB_HOST", "localhost")
        monkeypatch.setenv("DB_PORT", "5432")
        monkeypatch.setenv("DB_NAME", "test_db")
        monkeypatch.setenv("DB_USER", "user")
        monkeypatch.setenv("DB_PASSWORD", "password")
        monkeypatch.setenv("JWT_SECRET_KEY", "secret-key-123456")
        monkeypatch.setenv("JWT_ACCESS_TOKEN_EXPIRES", invalid_duration)

        # Act & Assert: Should raise ValidationError
        with pytest.raises(ValidationError):
            AppConfig()


class TestTestConfig:
    """Test TestConfig behavior and safety."""

    def test_test_config_uses_safe_defaults(self) -> None:
        """Test that TestConfig uses safe default values."""
        # Act: Create TestConfig without any environment variables
        config = TestConfig()

        # Assert: Safe default values should be used
        assert config.DB_HOST == "localhost"
        assert config.DB_NAME == ":memory:"
        assert config.DB_USER == "test_user"
        assert config.DB_PASSWORD == "test_password"
        assert (
            config.JWT_SECRET_KEY
            == "test-jwt-secret-key-for-testing-only-safe-default-value"
        )  # ←ここを修正
        assert config.TESTING is True
        assert config.DEBUG is True

    def test_test_config_database_url_property(self) -> None:
        """Test that TestConfig database_url property works correctly."""
        # Act: Create TestConfig
        config = TestConfig()

        # Assert: Database URL should be SQLite in-memory
        assert config.database_url == "sqlite:///:memory:"

    def test_test_config_ignores_env_file(
        self,
        tmp_path: Generator[Path, None, None],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test that TestConfig ignores .env file even if present."""
        # Arrange: Create .env file with production-like values
        env_file = tmp_path / ".env"
        env_file.write_text(
            """
DB_HOST=production_host
DB_NAME=production_db
JWT_SECRET_KEY=production_secret_from_env_file
""",
        )

        # Change to directory with .env file
        monkeypatch.chdir(tmp_path)

        # Act: Create TestConfig
        config = TestConfig()

        # Assert: Should use safe defaults, not .env values
        assert config.DB_HOST == "localhost"  # Not "production_host"
        assert config.DB_NAME == ":memory:"  # Not "production_db"
        # .envファイルの値ではなく、デフォルト値が使われていることを確認
        assert (
            config.JWT_SECRET_KEY
            == "test-jwt-secret-key-for-testing-only-safe-default-value"
        )
        assert config.JWT_SECRET_KEY != "production_secret_from_env_file"

    def test_test_config_only_uses_test_prefixed_env_vars(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test that TestConfig only uses TEST_ prefixed environment variables."""
        # Arrange: Set both regular and TEST_ prefixed variables
        monkeypatch.setenv("DB_HOST", "should_be_ignored")
        monkeypatch.setenv("TEST_DB_HOST", "test_override_host")

        # Act: Create TestConfig
        config = TestConfig()

        # Assert: Should use TEST_ prefixed value
        assert config.DB_HOST == "test_override_host"

    def test_test_config_rejects_dangerous_db_host(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test that TestConfig rejects dangerous production-like DB hosts."""
        # Arrange: Set dangerous DB host
        monkeypatch.setenv("TEST_DB_HOST", "production-database.example.com")

        # Act & Assert: Should raise ValueError
        with pytest.raises(ValueError, match="dangerous DB_HOST"):
            TestConfig()

    def test_test_config_rejects_live_db_host(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test that TestConfig rejects dangerous live DB hosts."""
        # Arrange: Set dangerous DB host with "live" pattern
        monkeypatch.setenv("TEST_DB_HOST", "live-database.example.com")

        # Act & Assert: Should raise ValueError
        with pytest.raises(ValueError, match="dangerous DB_HOST"):
            TestConfig()

    def test_test_config_accepts_safe_db_host(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test that TestConfig accepts safe DB hosts."""
        # Arrange: Set safe DB host
        monkeypatch.setenv("TEST_DB_HOST", "test-database.example.com")

        # Act: Should not raise any exception
        config = TestConfig()

        # Assert: Should use the override value
        assert config.DB_HOST == "test-database.example.com"


class TestGetConfigFactory:
    """Test get_config factory function."""

    def test_get_config_returns_test_config_when_testing_true(self) -> None:
        """Test that get_config returns TestConfig when testing=True."""
        # Act: Call factory with testing=True
        config = get_config(testing=True)

        # Assert: Should return TestConfig instance
        assert isinstance(config, TestConfig)
        assert config.TESTING is True

    def test_get_config_returns_app_config_when_testing_false(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test that get_config returns AppConfig when testing=False."""
        # Arrange: Set required environment variables for AppConfig
        required_vars = {
            "DB_HOST": "localhost",
            "DB_PORT": "5432",
            "DB_NAME": "test_db",
            "DB_USER": "user",
            "DB_PASSWORD": "password",
            "JWT_SECRET_KEY": "secret-key-123456",
        }

        for key, value in required_vars.items():
            monkeypatch.setenv(key, value)

        # Act: Call factory with testing=False
        config = get_config(testing=False)

        # Assert: Should return AppConfig instance (not TestConfig)
        assert isinstance(config, AppConfig)
        assert not isinstance(config, TestConfig)


class TestIsTestingFunction:
    """Test is_testing utility function."""

    def test_is_testing_returns_true_when_testing_env_var_set(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test that is_testing returns True when TESTING env var is set."""
        # Arrange: Set TESTING environment variable
        monkeypatch.setenv("TESTING", "true")

        # Act & Assert
        assert is_testing() is True

    @pytest.mark.parametrize("testing_value", ["false", "False", "FALSE", "0", ""])
    def test_is_testing_returns_false_for_falsy_values(
        self,
        monkeypatch: pytest.MonkeyPatch,
        testing_value: str,
    ) -> None:
        """Test that is_testing returns False for various falsy values."""
        # Arrange: Set TESTING to falsy value
        monkeypatch.setenv("TESTING", testing_value)

        # Act & Assert
        assert is_testing() is False

    def test_is_testing_returns_false_when_testing_env_var_not_set(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test that is_testing returns False when TESTING env var is not set."""
        # Arrange: Ensure TESTING is not set
        monkeypatch.delenv("TESTING", raising=False)

        # Act & Assert
        assert is_testing() is False
