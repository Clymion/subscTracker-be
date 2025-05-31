"""
Configuration fixtures for testing.

Minimal fixtures to support config testing without complex abstractions.
"""

import os
from typing import Any, Dict
from unittest.mock import patch

import pytest

from app.config import TestConfig


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment() -> None:
    """
    Set up test environment to prevent production config loading.

    This fixture runs automatically and ensures test safety.
    """
    # Mark that we're in testing mode
    os.environ["TESTING"] = "true"

    # Check for dangerous production variables
    dangerous_vars = [
        "PROD_DB_PASSWORD",
        "PROD_JWT_SECRET",
        "PRODUCTION",
        "DATABASE_URL",  # Common production DB var
        "REDIS_URL",  # Common production cache var
    ]

    for var in dangerous_vars:
        if var in os.environ:
            pytest.fail(
                f"Dangerous production variable '{var}' detected. "
                "Please unset this variable before running tests."
            )


@pytest.fixture
def clean_env(monkeypatch: pytest.MonkeyPatch):
    """
    Provide a clean environment for testing.

    Removes all config-related environment variables to ensure test isolation.
    """
    config_vars = [
        "DB_HOST",
        "DB_PORT",
        "DB_NAME",
        "DB_USER",
        "DB_PASSWORD",
        "JWT_SECRET_KEY",
        "API_PORT",
        "DEBUG",
        "JWT_ACCESS_TOKEN_EXPIRES",
        "JWT_REFRESH_TOKEN_EXPIRES",
        "ENABLE_NEW_BILLING",
    ]

    for var in config_vars:
        monkeypatch.delenv(var, raising=False)
        monkeypatch.delenv(f"TEST_{var}", raising=False)


@pytest.fixture
def required_env_vars(monkeypatch: pytest.MonkeyPatch) -> Dict[str, str]:
    """
    Set up all required environment variables for AppConfig.

    Returns the dictionary of set variables for test assertions.
    """
    vars_dict = {
        "DB_HOST": "test_host",
        "DB_PORT": "5432",
        "DB_NAME": "test_db",
        "DB_USER": "test_user",
        "DB_PASSWORD": "test_password",
        "JWT_SECRET_KEY": "test-secret-key-for-testing-123456",
    }

    for key, value in vars_dict.items():
        monkeypatch.setenv(key, value)

    return vars_dict
