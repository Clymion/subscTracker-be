"""
Initialization module for the SQLAlchemy models in the Flask application.

It sets up the database connection and ensures that all models are registered with SQLAlchemy.
"""
from sqlite3 import Connection as SQLiteConnection

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event
from sqlalchemy.engine import Engine


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection: SQLiteConnection, _connection_record) -> None:
    """Enable foreign key constraints for SQLite connections."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys = ON")
    cursor.close()


db = SQLAlchemy()


# Import all models here to register them with SQLAlchemy
from app.models.association_tables import subscription_labels
from app.models.label import Label
from app.models.subscription import Subscription
from app.models.user import User

# 他のモデルも同様にインポートしていく
