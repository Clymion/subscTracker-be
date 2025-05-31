"""
Main conftest.py for pytest configuration.

This file contains essential fixtures for testing without complex abstractions.
Focus on clarity and simplicity over sophisticated patterns.
"""

from collections.abc import Generator

import pytest
from flask import Flask
from flask.testing import FlaskClient
from flask_jwt_extended import JWTManager
from sqlalchemy.orm import Session

from app import create_app
from app.config import TestConfig, get_config
from app.models import db as _db
from tests.helpers import clean_database


@pytest.fixture(scope="session")
def test_config() -> TestConfig:
    """
    Provide test configuration.

    Returns:
        TestConfig: Test configuration instance.
    """
    return get_config(testing=True)


@pytest.fixture(scope="session")
def app(test_config: TestConfig) -> Generator[Flask, None, None]:
    """
    Create Flask application for testing.

    Args:
        test_config: Test configuration instance.

    Yields:
        Flask: Configured Flask application.
    """
    app = create_app()

    # Apply test configuration
    app.config.update(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": test_config.database_url,
            "SQLALCHEMY_TRACK_MODIFICATIONS": False,
            "JWT_SECRET_KEY": test_config.JWT_SECRET_KEY,
            "DEBUG": test_config.DEBUG,
        },
    )

    # Initialize JWT
    jwt_manager = JWTManager()
    jwt_manager.init_app(app)

    # Create database tables
    with app.app_context():
        _db.create_all()
        yield app
        _db.drop_all()


@pytest.fixture
def client(app: Flask) -> FlaskClient:
    """
    Provide Flask test client.

    Args:
        app: Flask application instance.

    Returns:
        FlaskClient: Test client for making HTTP requests.
    """
    return app.test_client()


@pytest.fixture
def db_session(app: Flask) -> Generator[Session, None, None]:
    """
    Provide database session with transaction rollback.

    Args:
        app: Flask application instance.

    Yields:
        Session: Database session for testing.
    """
    with app.app_context():
        # Create connection and begin transaction
        connection = _db.engine.connect()
        transaction = connection.begin()

        # Create session bound to the connection
        session = _db.sessionmaker(bind=connection)()

        # Make this session available to the app
        _db.session = session

        yield session

        # Cleanup: rollback transaction and close connection
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def clean_db(db_session: Session) -> Generator[Session, None, None]:
    """
    Provide clean database session.

    Args:
        db_session: Database session instance.

    Yields:
        Session: Clean database session.
    """
    # Clean up any existing data
    clean_database(db_session)

    yield db_session

    # Clean up after test
    clean_database(db_session)


# Test categorization markers
def pytest_configure(config):
    """Configure pytest markers for test categorization."""
    config.addinivalue_line(
        "markers",
        "unit: Unit tests that test individual components in isolation",
    )
    config.addinivalue_line(
        "markers",
        "integration: Integration tests that test component interactions",
    )
    config.addinivalue_line(
        "markers",
        "api: API tests that test HTTP endpoints end-to-end",
    )
    config.addinivalue_line(
        "markers",
        "auth: Tests related to authentication and authorization",
    )
    config.addinivalue_line(
        "markers",
        "slow: Tests that are slow to run",
    )


def pytest_collection_modifyitems(config, items):
    """Add markers based on test location and content."""
    for item in items:
        # Add markers based on test file location
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "api" in str(item.fspath) or "test_api" in item.name:
            item.add_marker(pytest.mark.api)

        # Add markers based on test content
        if "auth" in item.name.lower() or "login" in item.name.lower():
            item.add_marker(pytest.mark.auth)

        # Add database marker for tests using db fixtures
        if any(fixture in item.fixturenames for fixture in ["db_session", "clean_db"]):
            item.add_marker(pytest.mark.database)
