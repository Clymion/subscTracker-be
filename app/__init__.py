from flask import Flask
from flask_jwt_extended import JWTManager

from app.api.v1.auth import auth_bp
from app.api.v1.label import label_bp
from app.api.v1.subscription import subscription_bp
from app.api.v1.swagger import swagger_spec_bp, swagger_ui_bp
from app.api.v1.system import system_bp
from app.common.error_handlers import register_error_handlers
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

    # Initialize JWT manager
    jwt = JWTManager(app)
    jwt.init_app(app)

    # Register error handlers
    register_error_handlers(app)

    # Setup logging
    setup_logging(app)

    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix="/api/v1/auth")
    app.register_blueprint(subscription_bp, url_prefix="/api/v1")
    app.register_blueprint(label_bp, url_prefix="/api/v1")

    # OpenAPI仕様書(JSON)を配信するBlueprintを登録
    app.register_blueprint(swagger_spec_bp, url_prefix="/api/v1")
    app.register_blueprint(swagger_ui_bp)

    # システム監視用のBlueprintを登録
    app.register_blueprint(system_bp, url_prefix="/api/v1")

    return app
