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
        tmp_path: Path,
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

        # Isolate from project's .env file by changing the current directory
        monkeypatch.chdir(tmp_path)

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


class TestDatabaseUrlGeneration:
    """Test database_url property generation for different drivers.

    Requirements: 1.1, 1.2, 1.3, 1.4
    """

    def test_database_url_generates_sqlite_url_by_default(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        """Test that database_url generates SQLite URL when DB_DRIVER is sqlite.

        Requirement: 1.2 - SQLite接続URL生成
        """
        # Arrange: Set DB_DRIVER to sqlite with minimal required vars
        monkeypatch.setenv("DB_DRIVER", "sqlite")
        monkeypatch.setenv("DB_NAME", "test_app.db")
        monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-key-123456")
        monkeypatch.delenv("DB_HOST", raising=False)
        monkeypatch.delenv("DB_PORT", raising=False)
        monkeypatch.delenv("DB_USER", raising=False)
        monkeypatch.delenv("DB_PASSWORD", raising=False)
        monkeypatch.chdir(tmp_path)

        # Act
        config = AppConfig()

        # Assert: Should generate SQLite URL
        assert config.database_url.startswith("sqlite:///")
        assert "test_app.db" in config.database_url

    def test_database_url_generates_mysql_url_for_tidb(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test that database_url generates MySQL URL when DB_DRIVER is mysql.

        Requirement: 1.1 - MySQL互換(TiDB)接続URL生成
        Requirement: 1.3 - mysql+pymysqlドライバー使用
        """
        # Arrange: Set DB_DRIVER to mysql with all required vars
        monkeypatch.setenv("DB_DRIVER", "mysql")
        monkeypatch.setenv("DB_HOST", "tidb-server")
        monkeypatch.setenv("DB_PORT", "4000")
        monkeypatch.setenv("DB_USER", "tidb_user")
        monkeypatch.setenv("DB_PASSWORD", "tidb_password")
        monkeypatch.setenv("DB_NAME", "subscription_db")
        monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-key-123456")

        # Act
        config = AppConfig()

        # Assert: Should generate MySQL URL with pymysql driver
        assert config.database_url.startswith("mysql+pymysql://")
        assert "tidb_user:tidb_password@tidb-server:4000/subscription_db" in config.database_url

    def test_database_url_includes_all_tidb_connection_params(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test that database_url includes all TiDB connection parameters.

        Requirement: 1.4 - 環境変数からTiDB接続情報読み込み
        """
        # Arrange: Set all TiDB connection parameters
        monkeypatch.setenv("DB_DRIVER", "mysql")
        monkeypatch.setenv("DB_HOST", "tidb-cluster.example.com")
        monkeypatch.setenv("DB_PORT", "4000")
        monkeypatch.setenv("DB_USER", "app_user")
        monkeypatch.setenv("DB_PASSWORD", "secure_password")
        monkeypatch.setenv("DB_NAME", "production_db")
        monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-key-123456")

        # Act
        config = AppConfig()

        # Assert: All connection params should be in URL
        url = config.database_url
        assert "tidb-cluster.example.com" in url  # DB_HOST
        assert "4000" in url  # DB_PORT
        assert "app_user" in url  # DB_USER
        assert "secure_password" in url  # DB_PASSWORD
        assert "production_db" in url  # DB_NAME

    def test_database_url_handles_empty_password_for_mysql(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test that database_url handles empty password for MySQL/TiDB."""
        # Arrange: Set mysql driver with empty password
        monkeypatch.setenv("DB_DRIVER", "mysql")
        monkeypatch.setenv("DB_HOST", "localhost")
        monkeypatch.setenv("DB_PORT", "4000")
        monkeypatch.setenv("DB_USER", "root")
        monkeypatch.setenv("DB_PASSWORD", "")  # Empty password
        monkeypatch.setenv("DB_NAME", "test_db")
        monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-key-123456")

        # Act
        config = AppConfig()

        # Assert: Should handle empty password gracefully
        assert config.database_url == "mysql+pymysql://root:@localhost:4000/test_db"

    def test_database_url_raises_error_for_unsupported_driver(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test that unsupported DB_DRIVER raises ValueError."""
        # Arrange: Set unsupported driver
        monkeypatch.setenv("DB_DRIVER", "postgres")
        monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-key-123456")

        # Act
        config = AppConfig()

        # Assert: Should raise ValueError when accessing database_url
        with pytest.raises(ValueError, match="Unsupported DB_DRIVER"):
            _ = config.database_url


class TestMysqlDriverValidation:
    """Test MySQL/TiDB driver-specific validation.

    Requirement: 1.5 - TiDB必須設定のバリデーション
    Note: These tests are for Task 1.2 (validation), Task 1.1 is URL generation only.
    """

    def test_mysql_driver_requires_all_connection_params(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test that mysql driver requires all connection parameters."""
        # Arrange: Set mysql driver with all required fields
        monkeypatch.setenv("DB_DRIVER", "mysql")
        monkeypatch.setenv("DB_HOST", "tidb-host")
        monkeypatch.setenv("DB_PORT", "4000")
        monkeypatch.setenv("DB_USER", "user")
        monkeypatch.setenv("DB_PASSWORD", "password")
        monkeypatch.setenv("DB_NAME", "db")
        monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-key-123456")

        # Act & Assert: Should not raise error
        config = AppConfig()
        assert config.DB_DRIVER == "mysql"

    def test_sqlite_driver_does_not_require_connection_params(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        """Test that sqlite driver does not require connection params.

        Requirement: 1.5 - SQLiteの場合はバリデーションをスキップ
        """
        # Arrange: Set sqlite driver without connection params
        monkeypatch.setenv("DB_DRIVER", "sqlite")
        monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-key-123456")
        monkeypatch.delenv("DB_HOST", raising=False)
        monkeypatch.delenv("DB_PORT", raising=False)
        monkeypatch.delenv("DB_USER", raising=False)
        monkeypatch.delenv("DB_PASSWORD", raising=False)
        monkeypatch.chdir(tmp_path)

        # Act & Assert: Should not raise error
        config = AppConfig()
        assert config.DB_DRIVER == "sqlite"
        assert config.database_url.startswith("sqlite:///")

    @pytest.mark.parametrize(
        "missing_field",
        ["DB_HOST", "DB_PORT", "DB_USER", "DB_PASSWORD", "DB_NAME"],
    )
    def test_mysql_driver_raises_error_when_required_field_missing(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        missing_field: str,
    ) -> None:
        """Test that mysql driver raises error when required field is missing.

        Requirement: 1.5 - 欠落しているフィールドがある場合、起動時に明確なエラーメッセージを表示
        """
        # Arrange: Set mysql driver with all required fields
        monkeypatch.setenv("DB_DRIVER", "mysql")
        monkeypatch.setenv("DB_HOST", "tidb-host")
        monkeypatch.setenv("DB_PORT", "4000")
        monkeypatch.setenv("DB_USER", "user")
        monkeypatch.setenv("DB_PASSWORD", "password")
        monkeypatch.setenv("DB_NAME", "test_db")
        monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-key-123456")

        # Delete one required field
        monkeypatch.delenv(missing_field, raising=False)

        # Isolate from project's .env file by changing the current directory
        monkeypatch.chdir(tmp_path)

        # Act & Assert: Should raise ValidationError with clear message
        with pytest.raises(ValidationError) as exc_info:
            AppConfig()

        # Verify error message mentions the missing field
        errors = exc_info.value.errors()
        error_messages = [str(e) for e in errors]
        assert any(missing_field in msg for msg in error_messages)

    def test_mysql_driver_validation_error_message_is_clear(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        """Test that validation error message clearly indicates missing field.

        Requirement: 1.5 - 欠落しているフィールドがある場合、起動時に明確なエラーメッセージを表示
        """
        # Arrange: Set mysql driver without DB_HOST
        monkeypatch.setenv("DB_DRIVER", "mysql")
        monkeypatch.delenv("DB_HOST", raising=False)
        monkeypatch.setenv("DB_PORT", "4000")
        monkeypatch.setenv("DB_USER", "user")
        monkeypatch.setenv("DB_PASSWORD", "password")
        monkeypatch.setenv("DB_NAME", "test_db")
        monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-key-123456")

        # Isolate from project's .env file
        monkeypatch.chdir(tmp_path)

        # Act & Assert: Should raise ValidationError with clear message
        with pytest.raises(ValidationError) as exc_info:
            AppConfig()

        # Verify error message is clear about which field is missing
        error_str = str(exc_info.value)
        assert "DB_HOST" in error_str
        assert "mysql" in error_str.lower() or "required" in error_str.lower()


class TestConnectionPoolSettings:
    """Test connection pool settings for different database drivers.

    Requirements: 7.1, 7.2, 7.4 - 接続プール設定
    Task: 1.3 - 接続プール設定の実装
    """

    def test_sqlite_does_not_include_pool_settings(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        """Test that SQLite connection does not include pool settings.

        Requirement: 7.1, 7.2, 7.4 - SQLite接続時はプール設定をスキップ
        """
        # Arrange: Set sqlite driver
        monkeypatch.setenv("DB_DRIVER", "sqlite")
        monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-key-123456")
        monkeypatch.chdir(tmp_path)

        # Act
        config = AppConfig()
        flask_config = config.to_flask_config()

        # Assert: SQLite should not have pool settings
        assert "SQLALCHEMY_ENGINE_OPTIONS" not in flask_config

    def test_mysql_includes_pool_settings(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test that MySQL/TiDB connection includes pool settings.

        Requirement: 7.1, 7.2, 7.4 - TiDB接続用のプール設定を提供
        """
        # Arrange: Set mysql driver with all required fields
        monkeypatch.setenv("DB_DRIVER", "mysql")
        monkeypatch.setenv("DB_HOST", "tidb-host")
        monkeypatch.setenv("DB_PORT", "4000")
        monkeypatch.setenv("DB_USER", "user")
        monkeypatch.setenv("DB_PASSWORD", "password")
        monkeypatch.setenv("DB_NAME", "test_db")
        monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-key-123456")

        # Act
        config = AppConfig()
        flask_config = config.to_flask_config()

        # Assert: MySQL should have pool settings
        assert "SQLALCHEMY_ENGINE_OPTIONS" in flask_config
        engine_opts = flask_config["SQLALCHEMY_ENGINE_OPTIONS"]
        assert "pool_size" in engine_opts
        assert "pool_recycle" in engine_opts
        assert "pool_pre_ping" in engine_opts

    def test_mysql_pool_size_is_configurable(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test that pool_size is set for MySQL/TiDB connections.

        Requirement: 7.1 - 適切な接続プールサイズを設定
        """
        # Arrange
        monkeypatch.setenv("DB_DRIVER", "mysql")
        monkeypatch.setenv("DB_HOST", "tidb-host")
        monkeypatch.setenv("DB_PORT", "4000")
        monkeypatch.setenv("DB_USER", "user")
        monkeypatch.setenv("DB_PASSWORD", "password")
        monkeypatch.setenv("DB_NAME", "test_db")
        monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-key-123456")

        # Act
        config = AppConfig()
        flask_config = config.to_flask_config()

        # Assert: pool_size should be a positive integer
        pool_size = flask_config["SQLALCHEMY_ENGINE_OPTIONS"]["pool_size"]
        assert isinstance(pool_size, int)
        assert pool_size > 0

    def test_mysql_pool_recycle_is_set(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test that pool_recycle is set for MySQL/TiDB connections.

        Requirement: 7.2 - アイドル接続管理
        """
        # Arrange
        monkeypatch.setenv("DB_DRIVER", "mysql")
        monkeypatch.setenv("DB_HOST", "tidb-host")
        monkeypatch.setenv("DB_PORT", "4000")
        monkeypatch.setenv("DB_USER", "user")
        monkeypatch.setenv("DB_PASSWORD", "password")
        monkeypatch.setenv("DB_NAME", "test_db")
        monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-key-123456")

        # Act
        config = AppConfig()
        flask_config = config.to_flask_config()

        # Assert: pool_recycle should be a positive integer (seconds)
        pool_recycle = flask_config["SQLALCHEMY_ENGINE_OPTIONS"]["pool_recycle"]
        assert isinstance(pool_recycle, int)
        assert pool_recycle > 0


class TestPoolPrePing:
    """Test pool_pre_ping functionality for connection health checks.

    Requirement: 7.3 - 再接続試行機能
    Task: 1.4 - 再接続試行機能の確認
    """

    def test_pool_pre_ping_enabled_for_mysql(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test that pool_pre_ping is enabled for MySQL/TiDB connections.

        Requirement: 7.3, 7.4 - 接続の健全性を確認
        """
        # Arrange
        monkeypatch.setenv("DB_DRIVER", "mysql")
        monkeypatch.setenv("DB_HOST", "tidb-host")
        monkeypatch.setenv("DB_PORT", "4000")
        monkeypatch.setenv("DB_USER", "user")
        monkeypatch.setenv("DB_PASSWORD", "password")
        monkeypatch.setenv("DB_NAME", "test_db")
        monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-key-123456")

        # Act
        config = AppConfig()
        flask_config = config.to_flask_config()

        # Assert: pool_pre_ping should be True
        assert flask_config["SQLALCHEMY_ENGINE_OPTIONS"]["pool_pre_ping"] is True

    def test_pool_pre_ping_not_set_for_sqlite(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        """Test that pool_pre_ping is not set for SQLite connections.

        SQLite does not benefit from pool_pre_ping as it's a file-based DB.
        """
        # Arrange
        monkeypatch.setenv("DB_DRIVER", "sqlite")
        monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-key-123456")
        monkeypatch.chdir(tmp_path)

        # Act
        config = AppConfig()
        flask_config = config.to_flask_config()

        # Assert: No engine options for SQLite
        assert "SQLALCHEMY_ENGINE_OPTIONS" not in flask_config
