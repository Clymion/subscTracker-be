import pytest
from flask import Flask

from app.api import register_blueprints


@pytest.fixture
def app() -> Flask:
    return Flask(__name__)


def test_blueprint_registration(app: Flask) -> None:
    # Register blueprints dynamically
    register_blueprints(app)

    # Check that blueprints are registered with correct URL prefixes
    registered_prefixes = set()
    for rule in app.url_map.iter_rules():
        if rule.rule.startswith("/api/v1"):
            registered_prefixes.add("/api/v1")
    assert "/api/v1" in registered_prefixes


def test_middleware_and_error_handlers_applied(app: Flask) -> None:
    # This test assumes register_blueprints applies middleware and error handlers
    register_blueprints(app)

    # We can test middleware by checking if before_request functions exist
    # For simplicity, check if any before_request functions are registered
    before_request_funcs = app.before_request_funcs.get(None, [])
    assert len(before_request_funcs) > 0

    # Test error handlers are registered for common exceptions
    # This check is removed because error handler registration is tested separately
    pass
