import importlib
from pathlib import Path

from flask import Blueprint, Flask

from app.common.errors import register_error_handlers


def register_blueprints(app: Flask) -> Flask:
    """
    Dynamically register all blueprints from versioned API folders under app/api/

    Applies URL prefixes and registers error handlers and middleware.
    """
    base_api_path = Path(__file__).parent
    # List all subdirectories in app/api that start with 'v' (e.g., v1, v2)
    version_dirs = [
        d.name for d in base_api_path.iterdir() if d.is_dir() and d.name.startswith("v")
    ]

    for version in version_dirs:
        module_name = f"app.api.{version}"
        try:
            module = importlib.import_module(module_name)
        except ImportError:
            continue

        # Expect each version module to have a 'bp' Blueprint instance
        bp = getattr(module, "bp", None)
        if bp and isinstance(bp, Blueprint):
            # Register blueprint with URL prefix /api/{version}
            url_prefix = f"/api/{version}"
            app.register_blueprint(bp, url_prefix=url_prefix)

    # Register global error handlers
    register_error_handlers(app)
    return app

    # Example middleware: simple request logging
    @app.before_request
    def log_request():
        # Here you could add logging or other middleware logic
        pass
