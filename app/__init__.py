from flask import Flask
from flask_jwt_extended import JWTManager
from flask_sqlalchemy import SQLAlchemy

from app.api.v1 import bp as v1_bp
from app.config import Config

db = SQLAlchemy()
jwt = JWTManager()


def create_app(config_class: type[Config]) -> Flask:
    """Application factory to create Flask app instances."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    jwt.init_app(app)

    # Register blueprints here
    app.register_blueprint(v1_bp, url_prefix="/api/v1")

    return app
