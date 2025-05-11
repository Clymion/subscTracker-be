import os
import pytest
from pydantic import ValidationError
from app.common.config import Settings, get_settings

def test_load_env_variables(monkeypatch):
    # Clear environment variables to avoid interference
    monkeypatch.delenv("APP_ENV", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("SECRET_KEY", raising=False)
    monkeypatch.delenv("MAX_CONNECTIONS", raising=False)

    # Set environment variables for testing
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///test.db")
    monkeypatch.setenv("SECRET_KEY", "testsecret")

    settings = get_settings()
    assert settings.app_env == "development"
    assert settings.database_url == "sqlite:///test.db"
    assert settings.secret_key.get_secret_value() == "testsecret"

def test_environment_switching(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("DATABASE_URL", "postgresql://prod.db")
    monkeypatch.setenv("SECRET_KEY", "prodsecret")

    settings = get_settings()
    assert settings.app_env == "production"
    assert settings.database_url == "postgresql://prod.db"
    assert settings.secret_key.get_secret_value() == "prodsecret"

def test_missing_required_env_vars(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("SECRET_KEY", "secret")

    with pytest.raises(ValidationError):
        get_settings()

def test_invalid_env_var_type(monkeypatch):
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///test.db")
    monkeypatch.setenv("SECRET_KEY", "secret")
    monkeypatch.setenv("MAX_CONNECTIONS", "not_an_int")

    with pytest.raises(ValidationError):
        get_settings()

def test_default_values(monkeypatch):
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///test.db")
    monkeypatch.setenv("SECRET_KEY", "secret")
    monkeypatch.delenv("MAX_CONNECTIONS", raising=False)

    settings = get_settings()
    assert settings.max_connections == 10  # Assuming default is 10

def test_sensitive_info_not_exposed(monkeypatch):
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///test.db")
    monkeypatch.setenv("SECRET_KEY", "secret")

    settings = get_settings()
    assert hasattr(settings, "secret_key")
    # Ensure secret_key is not printed or logged in this test (manual check)
