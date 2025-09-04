"""Logging setup for the application."""

import logging
import sys
import time
from datetime import datetime
from logging import LogRecord
from logging.handlers import RotatingFileHandler
from zoneinfo import ZoneInfo

from flask import Flask, g
from flask.wrappers import Response

LOG_FILE = "logs/app.log"

JST = ZoneInfo("Asia/Tokyo")


class JSTFormatter(logging.Formatter):
    """Formatter to display time in JST."""

    def formatTime(
        self, record: LogRecord, datefmt: str | None = None
    ) -> str:  # noqa: N802
        """
        Format the time for the log record in JST.

        Args:
            record: The log record.
            datefmt: The date format string.

        Returns:
            The formatted time string.
        """
        dt = datetime.fromtimestamp(record.created, JST)
        if datefmt:
            return dt.strftime(datefmt)
        return dt.isoformat()


def setup_logging(app: Flask) -> None:
    """
    Set up logging configuration for the Flask app.

    Args:
        app: The Flask application instance.

    """
    log_formatter = JSTFormatter(
        "%(asctime)s %(levelname)s [%(name)s] [%(pathname)s:%(lineno)d] %(message)s",
    )
    log_level = (
        "DEBUG"
        if app.config.get("DEBUG")
        else app.config.get("LOG_LEVEL", "INFO").upper()
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_formatter)
    console_handler.setLevel(log_level)

    # File handler with rotation
    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setFormatter(log_formatter)
    file_handler.setLevel(log_level)

    # Clear existing handlers, then add new handlers
    root_logger = logging.getLogger()
    # WerkzeugのログもキャッチするためにルートロガーのレベルをDEBUGに設定
    root_logger.setLevel(logging.DEBUG)
    root_logger.handlers.clear()
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    # Werkzeugのロガーにもハンドラを追加して、リクエストログもファイルに出す
    werkzeug_logger = logging.getLogger("werkzeug")
    werkzeug_logger.handlers.clear()
    werkzeug_logger.propagate = False  # 二重にログが出ないようにする
    werkzeug_logger.addHandler(console_handler)
    werkzeug_logger.addHandler(file_handler)

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
        # この関数はwerkzeugのログに任せる
        return response


def get_logger(name: str | None = None) -> logging.Logger:
    """
    Get a logger instance with the specified name.

    Args:
        name: The name of the logger.

    Returns:
        A logging.Logger instance.

    """
    # logging.getLogger(__name__) を直接使うのが一般的
    return logging.getLogger(name)
