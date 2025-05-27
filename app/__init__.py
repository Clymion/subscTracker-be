from flask import Flask
from app.models import db
from app.api.v1.auth import auth_bp
from app.common.logging_setup import setup_logging


def create_app():
    app = Flask(__name__)

    # Load configuration from environment or config files as needed
    app.config.from_envvar("APP_CONFIG_FILE", silent=True)

    # Initialize database
    db.init_app(app)

    # Setup logging
    setup_logging(app)

    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/api/v1/auth')

    return app
