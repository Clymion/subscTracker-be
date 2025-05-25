from flask import Flask

from app.common.logging_setup import setup_logging


def create_app():
    app = Flask(__name__)

    # Load configuration from environment or config files as needed
    app.config.from_envvar("APP_CONFIG_FILE", silent=True)

    # Setup logging
    setup_logging(app)

    # Import and register blueprints here (e.g., auth, subscriptions)
    # from app.api.v1.auth import auth_bp
    # app.register_blueprint(auth_bp, url_prefix='/api/v1/auth')

    return app
