import pytest
from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

from app import create_app
from app.database import Base, SessionLocal, engine

# Use an in-memory SQLite database for tests
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

# Create a new engine and session for testing
from sqlalchemy import create_engine

test_engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

# Override the Base metadata to use the test engine
Base.metadata.bind = test_engine


@pytest.fixture(scope="session")
def app():
    """Create and configure a new app instance for each test session."""
    app = create_app()
    app.config.update(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": SQLALCHEMY_DATABASE_URL,
            "WTF_CSRF_ENABLED": False,
        }
    )

    # Create tables
    with app.app_context():
        Base.metadata.create_all(bind=test_engine)

    yield app

    # Drop tables after tests
    with app.app_context():
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def db_session(app):
    """Creates a new database session for a test."""
    connection = test_engine.connect()
    transaction = connection.begin()

    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def client(app, db_session):
    """A test client for the app."""
    # Override the app's db session with the test session
    app.db_session = db_session
    with app.test_client() as client:
        yield client


# Helper function to reset database before each test if needed
@pytest.fixture(autouse=True)
def reset_db(db_session):
    """Reset database state before each test."""
    # Could add logic here if needed to reset data
    yield
    # Cleanup after test if needed
