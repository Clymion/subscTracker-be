"""Configuration module for the application."""
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppConfig(BaseSettings):
    """
    Application configuration using pydantic-settings BaseSettings for environment management.

    This class loads environment variables from a .env file and system environment,
    validates required fields, applies default values, and ensures type safety.
    """

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Database settings
    DB_HOST: str = Field(env="DB_HOST")
    DB_PORT: int = Field(env="DB_PORT")
    DB_NAME: str = Field(env="DB_NAME")
    DB_USER: str = Field(env="DB_USER")
    DB_PASSWORD: str = Field(env="DB_PASSWORD")

    # API settings
    API_PORT: int = Field(5000, env="API_PORT")
    DEBUG: bool = Field(False, env="DEBUG")

    # JWT settings
    JWT_SECRET_KEY: str = Field(env="JWT_SECRET_KEY")
    JWT_ACCESS_TOKEN_EXPIRES: int = Field(
        3600, env="JWT_ACCESS_TOKEN_EXPIRES",
    )  # seconds
    JWT_REFRESH_TOKEN_EXPIRES: int = Field(
        2592000, env="JWT_REFRESH_TOKEN_EXPIRES",
    )  # seconds

    # Feature flags
    ENABLE_NEW_BILLING: bool = Field(False, env="ENABLE_NEW_BILLING")

    @field_validator(
        "DB_PORT", "API_PORT", "JWT_ACCESS_TOKEN_EXPIRES", "JWT_REFRESH_TOKEN_EXPIRES",
    )
    @classmethod
    def check_positive(cls, v: int) -> int:
        """Validate that integer fields are positive."""
        if v is not None and v <= 0:
            msg = "Must be a positive integer"
            raise ValueError(msg)
        return v


def get_config() -> AppConfig:
    """Return a new AppConfig instance, loading environment variables at call time."""
    return AppConfig()
