import logging
import time
from logging.handlers import RotatingFileHandler

from flask import Flask, g, request
from flask.wrappers import Response


def setup_logging(app: Flask) -> None:
    """
    Set up logging configuration for the Flask app.

    Args:
        app: The Flask application instance.

    """
    log_formatter = logging.Formatter(
        "%(asctime)s %(levelname)s [%(name)s] %(message)s"
    )
    log_level = app.config.get("LOG_LEVEL", "INFO").upper()

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_formatter)
    console_handler.setLevel(log_level)

    # File handler with rotation
    file_handler = RotatingFileHandler(
        "logs/app.log", maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8"
    )
    file_handler.setFormatter(log_formatter)
    file_handler.setLevel(log_level)

    # Clear existing handlers, then add new handlers
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.handlers.clear()
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    @app.before_request
    def start_timer() -> None:
        """Start timer before request to measure duration."""
        g.start_time = time.time()

    @app.after_request
    def log_request_response(response: Response) -> Response:
        """
        Log details of the request and response.

        Args:
            response: The Flask response object.

        Returns:
            The same response object.

        """
        # Calculate duration of the request
        duration = -1.0 if not hasattr(g, "start_time") else time.time() - g.start_time

        client_ip = request.headers.get("X-Forwarded-For", request.remote_addr)
        method = request.method
        path = request.path
        status_code = response.status_code
        user_agent = request.headers.get("User-Agent", "")
        content_length = response.content_length or 0

        log_params = {
            "method": method,
            "path": path,
            "status_code": status_code,
            "duration": round(duration, 4),
            "client_ip": client_ip,
            "user_agent": user_agent,
            "content_length": content_length,
        }

        log_message = (
            f"{log_params['client_ip']} {log_params['method']} {log_params['path']} "
            f"Status: {log_params['status_code']} Duration: {log_params['duration']}s "
            f"Size: {log_params['content_length']} UA: {log_params['user_agent']}"
        )

        if status_code >= 500:
            logging.error(log_message)
        elif status_code >= 400:
            logging.warning(log_message)
        else:
            logging.info(log_message)

        return response
