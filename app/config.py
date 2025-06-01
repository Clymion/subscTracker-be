"""Configuration module for the application."""

from typing import ClassVar, Self

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppConfig(BaseSettings):
    """
    Application configuration using pydantic-settings BaseSettings for environment management.

    This class loads environment variables from a .env file and system environment,
    validates required fields, applies default values, and ensures type safety.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",  # 未定義の環境変数を無視
    )

    # Database settings - すべて必須
    DB_HOST: str = Field(description="Database host")
    DB_PORT: int = Field(description="Database port")
    DB_NAME: str = Field(description="Database name")
    DB_USER: str = Field(description="Database user")
    DB_PASSWORD: str = Field(description="Database password")

    # API settings - デフォルト値あり
    API_PORT: int = Field(default=5000, description="API server port")
    DEBUG: bool = Field(default=False, description="Debug mode flag")

    # JWT settings - SECRET_KEYは必須、期限はデフォルトあり
    JWT_SECRET_KEY: str = Field(description="JWT secret key")
    JWT_ACCESS_TOKEN_EXPIRES: int = Field(
        default=3600, description="JWT access token expiration in seconds"
    )
    JWT_REFRESH_TOKEN_EXPIRES: int = Field(
        default=2592000, description="JWT refresh token expiration in seconds"
    )

    # Feature flags - デフォルト値あり
    ENABLE_NEW_BILLING: bool = Field(
        default=False, description="Enable new billing feature"
    )

    @field_validator("DB_PORT", "API_PORT")
    @classmethod
    def validate_port_range(cls, v: int) -> int:
        """ポート番号が有効な範囲内であることを検証"""
        if v <= 0 or v > 65535:
            msg = "Port must be between 1 and 65535"
            raise ValueError(msg)
        return v

    @field_validator("JWT_ACCESS_TOKEN_EXPIRES", "JWT_REFRESH_TOKEN_EXPIRES")
    @classmethod
    def validate_positive_duration(cls, v: int) -> int:
        """時間設定が正の値であることを検証"""
        if v <= 0:
            msg = "Duration must be positive"
            raise ValueError(msg)
        return v

    @field_validator("JWT_SECRET_KEY")
    @classmethod
    def validate_jwt_secret_length(cls, v: str) -> str:
        """JWT秘密鍵の長さを検証"""
        if len(v) < 16:
            msg = "JWT secret key must be at least 16 characters long"
            raise ValueError(msg)
        return v

    @property
    def database_url(self) -> str:
        """Generate SQLite database URL for production."""
        return f"sqlite:///{self.DB_NAME}"

    def to_flask_config(self) -> dict:
        """Convert to Flask test configuration format."""
        return {
            "SQLALCHEMY_DATABASE_URI": self.database_url,
            "SQLALCHEMY_TRACK_MODIFICATIONS": False,
            "JWT_SECRET_KEY": self.JWT_SECRET_KEY,
            "DEBUG": self.DEBUG,
            "TESTING": False,
        }


class TestConfig(BaseSettings):
    """
    Test-specific configuration class that provides safe defaults for testing.

    This class completely isolates test environment from production configuration
    by not loading any .env files and providing safe default values.
    """

    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(
        env_file=None,  # .envファイルを読み込まない
        env_prefix="TEST_",  # TEST_プレフィックスの環境変数のみ使用
        case_sensitive=True,
        extra="ignore",
    )

    # テスト用の安全なデフォルト値
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = ":memory:"  # SQLiteのインメモリDB
    DB_USER: str = "test_user"
    DB_PASSWORD: str = "test_password"  # noqa: S105

    # テスト用JWT設定("production"という文字を含まない安全な値)
    JWT_SECRET_KEY: str = (
        "test-jwt-secret-key-for-testing-only-safe-default-value"  # noqa: S105
    )
    JWT_ACCESS_TOKEN_EXPIRES: int = 3600
    JWT_REFRESH_TOKEN_EXPIRES: int = 86400  # 24時間(テスト用に短縮)

    # テスト環境フラグ
    API_PORT: int = 5000
    DEBUG: bool = True
    TESTING: bool = Field(default=True, frozen=True)  # 常にTrue

    # テスト用機能フラグ
    ENABLE_NEW_BILLING: bool = False

    @model_validator(mode="after")
    def validate_safe_test_config(self) -> Self:
        """テスト設定の安全性チェック"""
        # 本番用の値が混入していないかチェック
        dangerous_patterns = ["prod", "production", "live"]
        for pattern in dangerous_patterns:
            if pattern.lower() in self.DB_HOST.lower():
                msg = f"Test config contains dangerous DB_HOST: {self.DB_HOST}"
                raise ValueError(msg)
        return self

    @property
    def database_url(self) -> str:
        """テスト用データベースURL生成"""
        if self.DB_NAME == ":memory:":
            return "sqlite:///:memory:"
        return f"sqlite:///{self.DB_NAME}"

    def to_flask_config(self) -> dict:
        """Convert to Flask test configuration format."""
        return {
            "SQLALCHEMY_DATABASE_URI": self.database_url,
            "SQLALCHEMY_TRACK_MODIFICATIONS": False,
            "JWT_SECRET_KEY": self.JWT_SECRET_KEY,
            "DEBUG": self.DEBUG,
            "TESTING": True,
        }


def get_config(testing: bool = False) -> AppConfig | TestConfig:
    """
    Factory function to get appropriate configuration.

    Args:
        testing: If True, returns TestConfig instance with safe defaults.
                If False, returns AppConfig instance that loads from environment.

    Returns:
        AppConfig or TestConfig: Configuration instance appropriate for the environment.

    Raises:
        ValueError: If required environment variables are missing or invalid.
    """
    if testing:
        return TestConfig()
    return AppConfig()


# テスト実行中かどうかの判定
def is_testing() -> bool:
    """現在テスト実行中かどうかを判定"""
    import os

    return os.getenv("TESTING", "false").lower() == "true"
