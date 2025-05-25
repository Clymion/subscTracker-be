import pytest
from pydantic import ValidationError

from app.config import get_config


def test_load_env_variables(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that environment variables are correctly loaded into the config."""
    monkeypatch.setenv("DB_HOST", "localhost")
    monkeypatch.setenv("DB_PORT", "5432")
    monkeypatch.setenv("DB_NAME", "test_db")
    monkeypatch.setenv("DB_USER", "user")
    monkeypatch.setenv("DB_PASSWORD", "password")
    monkeypatch.setenv("JWT_SECRET_KEY", "supersecretkey")

    config = get_config()
    assert config.DB_HOST == "localhost"
    assert config.DB_PORT == 5432
    assert config.DB_NAME == "test_db"
    assert config.DB_USER == "user"
    assert config.DB_PASSWORD == "password"
    assert config.JWT_SECRET_KEY == "supersecretkey"


def test_missing_required_env_vars(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that missing required environment variables raise validation errors."""
    monkeypatch.delenv("DB_HOST", raising=False)
    monkeypatch.delenv("DB_PORT", raising=False)
    monkeypatch.delenv("DB_NAME", raising=False)
    monkeypatch.delenv("DB_USER", raising=False)
    monkeypatch.delenv("DB_PASSWORD", raising=False)
    monkeypatch.delenv("JWT_SECRET_KEY", raising=False)

    with pytest.raises(ValidationError):
        get_config()


def test_invalid_type_env_vars(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that invalid type environment variables raise validation errors."""
    monkeypatch.setenv("DB_PORT", "not_an_int")
    monkeypatch.setenv("DB_HOST", "localhost")
    monkeypatch.setenv("DB_NAME", "test_db")
    monkeypatch.setenv("DB_USER", "user")
    monkeypatch.setenv("DB_PASSWORD", "password")
    monkeypatch.setenv("JWT_SECRET_KEY", "supersecretkey")

    with pytest.raises(ValidationError):
        get_config()


def test_default_values(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that default values are applied when optional variables are not set."""
    monkeypatch.setenv("DB_HOST", "localhost")
    monkeypatch.setenv("DB_PORT", "5432")
    monkeypatch.setenv("DB_NAME", "test_db")
    monkeypatch.setenv("DB_USER", "user")
    monkeypatch.setenv("DB_PASSWORD", "password")
    monkeypatch.setenv("JWT_SECRET_KEY", "supersecretkey")

    config = get_config()
    assert config.API_PORT == 5000
    assert config.DEBUG is False


def test_config_attributes_types(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that config attributes have correct types and expected values."""
    monkeypatch.setenv("DB_HOST", "localhost")
    monkeypatch.setenv("DB_PORT", "5432")
    monkeypatch.setenv("DB_NAME", "test_db")
    monkeypatch.setenv("DB_USER", "user")
    monkeypatch.setenv("DB_PASSWORD", "password")
    monkeypatch.setenv("JWT_SECRET_KEY", "supersecretkey")

    config = get_config()
    assert isinstance(config.DB_HOST, str)
    assert isinstance(config.DB_PORT, int)
    assert isinstance(config.API_PORT, int)
    assert isinstance(config.DEBUG, bool)


def test_loading_config_multiple_times(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that loading config multiple times returns consistent results."""
    monkeypatch.setenv("DB_HOST", "localhost")
    monkeypatch.setenv("DB_PORT", "5432")
    monkeypatch.setenv("DB_NAME", "test_db")
    monkeypatch.setenv("DB_USER", "user")
    monkeypatch.setenv("DB_PASSWORD", "password")
    monkeypatch.setenv("JWT_SECRET_KEY", "supersecretkey")

    config1 = get_config()
    config2 = get_config()
    assert config1 == config2
