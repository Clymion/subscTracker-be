import os

import pytest
from flask import Flask
from flask.testing import FlaskClient, FlaskCliRunner

from app import create_app
from app.models import db as _db

# Configure environment variables for testing
os.environ["FLASK_ENV"] = "testing"
os.environ["FLASK_DEBUG"] = "0"


@pytest.fixture(scope="session")
def app() -> Flask:
    """
    Create and configure a new app instance for each test session.

    Returns:
        Flask: The configured Flask application instance.
    """
    app = create_app()
    app.config.update(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        },
    )

    with app.app_context():
        _db.create_all()
        yield app
        _db.drop_all()


@pytest.fixture
def session(app: Flask):
    """Create a database session for tests."""
    with app.app_context():
        connection = _db.engine.connect()
        transaction = connection.begin()

        session_options = {"bind": connection, "binds": {}}
        session = _db.sessionmaker(**session_options)()

        _db.session = session

        yield session

        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def client(app: Flask) -> FlaskClient:
    """
    Return a test client for the app.

    Args:
        app (Flask): The Flask application instance.

    Returns:
        FlaskClient: A test client for the Flask app.
    """
    return app.test_client()


@pytest.fixture
def runner(app: Flask) -> FlaskCliRunner:
    """
    Execute a test runner for the app's Click commands.

    Args:
        app (Flask): The Flask application instance.

    Returns:
        FlaskCliRunner: A test runner for the Flask app's CLI commands.
    """
    return app.test_cli_runner()


@pytest.fixture
def auth_headers() -> dict[str, str]:
    """
    Generate authentication headers for tests.

    Args:
        client (FlaskClient): The Flask test client.

    Returns:
        dict[str, str]: A dictionary containing the Authorization header.
    """
    # TODO: Implement token generation or mock authentication
    token = "test-token"
    return {"Authorization": f"Bearer {token}"}
