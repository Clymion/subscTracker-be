from flask import Flask
from flask_jwt_extended import JWTManager
from flask_sqlalchemy import SQLAlchemy

from app.config import Config

db = SQLAlchemy()
jwt = JWTManager()


def create_app(config_class=Config):
    """Application factory to create Flask app instances."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    jwt.init_app(app)

    # Register blueprints here (placeholders for now)
    # from app.api.v1.auth import auth_bp
    # app.register_blueprint(auth_bp)

    return app
