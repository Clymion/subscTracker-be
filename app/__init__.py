from flask import Flask

from app.api.v1.auth import auth_bp
from app.api.v1.subscription import subscription_bp  # これを追加
from app.common.logging_setup import setup_logging
from app.config import AppConfig, TestConfig, get_config
from app.models import db


def create_app(config_obj: AppConfig | TestConfig | None = None) -> Flask:
    """Create and configure the Flask application."""
    app = Flask(__name__)

    if config_obj:
        app.config.update(config_obj.to_flask_config())
    else:
        config = get_config(testing=False)
        app.config.update(config.to_flask_config())

    # Initialize database
    db.init_app(app)

    # Setup logging
    setup_logging(app)

    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix="/api/v1/auth")
    # subscription_bpを登録するのだ
    app.register_blueprint(subscription_bp, url_prefix="/api/v1")

    return app
