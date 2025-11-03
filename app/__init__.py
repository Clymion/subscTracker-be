"""Initialize the Flask application and its extensions."""
from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager

from app.api.v1.auth import auth_bp
from app.api.v1.exchange_rate import exchange_rate_bp
from app.api.v1.label import label_bp
from app.api.v1.subscription import subscription_bp
from app.api.v1.payment_history import payment_history_bp
from app.api.v1.swagger import swagger_spec_bp, swagger_ui_bp
from app.api.v1.system import system_bp
from app.common.error_handlers import register_error_handlers
from app.common.logging_setup import setup_logging
from app.config import AppConfig, TestConfig, get_config
from app.constants import ErrorMessages
from app.models import db


def create_app(config_obj: AppConfig | TestConfig | None = None) -> Flask:
    """Create and configure the Flask application."""
    app = Flask(__name__)

    config = config_obj if config_obj else get_config(testing=False)
    app.config.update(config.to_flask_config())

    # Initialize database
    db.init_app(app)

    # Initialize JWT manager
    jwt = JWTManager()

    @jwt.unauthorized_loader
    def unauthorized_callback(_reason: str) -> tuple:
        return jsonify({
            "error": {
                "code": 401,
                "name": "Unauthorized",
                "message": "Missing Authorization Header",
            },
        }), 401

    @jwt.invalid_token_loader
    def invalid_token_callback(_error: str) -> tuple:
        return jsonify({
            "error": {
                "code": 422,
                "name": "Unprocessable Entity",
                "message": "Token is invalid or malformed.",
            },
        }), 422

    @jwt.expired_token_loader
    def expired_token_callback(_jwt_header: dict, _jwt_payload: dict) -> tuple:
        return jsonify({
            "error": {
                "code": 401,
                "name": "Unauthorized",
                "message": ErrorMessages.TOKEN_EXPIRED,
            },
        }), 401

    jwt.init_app(app)

    # Enable CORS
    CORS(app, resources={r"/api/*": {"origins": config.ALLOWED_ORIGINS}})

    # Register error handlers
    register_error_handlers(app)

    # Setup logging
    setup_logging(app)

    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix="/api/v1/auth")
    app.register_blueprint(subscription_bp, url_prefix="/api/v1")
    app.register_blueprint(label_bp, url_prefix="/api/v1")
    app.register_blueprint(exchange_rate_bp, url_prefix="/api/v1")
    app.register_blueprint(payment_history_bp, url_prefix="/api/v1")

    # OpenAPI仕様書(JSON)を配信するBlueprintを登録
    app.register_blueprint(swagger_spec_bp, url_prefix="/api/v1")
    app.register_blueprint(swagger_ui_bp)

    # システム監視用のBlueprintを登録
    app.register_blueprint(system_bp, url_prefix="/api/v1")

    return app
