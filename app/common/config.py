import os
from typing import Literal

from dotenv import load_dotenv
from pydantic import SecretStr, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()  # Explicitly load .env file


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    This class uses Pydantic for validation and type checking.
    """

    app_env: Literal["development", "test", "production"]
    database_url: str
    secret_key: SecretStr
    max_connections: int = 10

    model_config = SettingsConfigDict(
        env_file=None,  # Disable pydantic's env_file loading since dotenv is used
        case_sensitive=True,
        extra="forbid",
    )

    def __init__(self) -> None:
        """Initialize settings by loading environment variables."""
        # Map environment variables to field names explicitly
        env_vars = {
            "app_env": os.getenv("APP_ENV"),
            "database_url": os.getenv("DATABASE_URL"),
            "secret_key": os.getenv("SECRET_KEY"),
            "max_connections": os.getenv("MAX_CONNECTIONS", 10),
        }
        # Convert max_connections to int if it's a string
        if isinstance(env_vars["max_connections"], str):
            try:
                env_vars["max_connections"] = int(env_vars["max_connections"])
            except ValueError:
                # Instead of raising ValueError here, let pydantic handle validation
                env_vars["max_connections"] = env_vars["max_connections"]
        super().__init__(**env_vars)


def get_settings() -> Settings:
    """
    Load and return the application settings from environment variables.

    Raises ValidationError if required variables are missing or invalid.
    """
    try:
        settings = Settings()
    except ValidationError as e:
        # TODO: Here you could log the error or handle it as needed
        raise e
    return settings
