from __future__ import annotations

from flask import jsonify, request
from werkzeug.exceptions import HTTPException

# Centralized error messages with internationalization support (simple example)
ERROR_MESSAGES = {
    "en": {
        "VALIDATION_ERROR": "Validation failed",
        "AUTHENTICATION_ERROR": "Authentication failed",
        "RESOURCE_NOT_FOUND": "Resource not found",
        "GENERIC_ERROR": "An unexpected error occurred",
    },
    "ja": {
        "VALIDATION_ERROR": "検証エラー",
        "AUTHENTICATION_ERROR": "認証エラー",
        "RESOURCE_NOT_FOUND": "リソースが見つかりません",
        "GENERIC_ERROR": "予期しないエラーが発生しました",
    },
}


def get_locale() -> str:
    # Simple locale detection from Accept-Language header
    accept_language = request.headers.get("Accept-Language", "en")
    if accept_language.startswith("ja"):
        return "ja"
    return "en"


def get_error_message(code: str, default_message: str) -> str:
    locale = get_locale()
    return ERROR_MESSAGES.get(locale, {}).get(code, default_message)


class APIError(Exception):
    """Base class for all API errors."""

    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 500,
        details: dict | None = None,
    ) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


class ValidationError(APIError):
    """Validation error for API requests."""

    def __init__(
        self, message: str, field: str | None = None, reason: str | None = None
    ) -> None:
        details = {}
        if field:
            details["field"] = field
        if reason:
            details["reason"] = reason
        super().__init__("VALIDATION_ERROR", message, 400, details)


class AuthenticationError(APIError):
    """Authentication error for API requests."""

    def __init__(self, message: str | None = None) -> None:
        msg = message or get_error_message(
            "AUTHENTICATION_ERROR",
            "Authentication failed",
        )
        super().__init__("AUTHENTICATION_ERROR", msg, 401)


class ResourceNotFoundError(APIError):
    """Resource not found error for API requests."""

    def __init__(self, message: str | None = None) -> None:
        msg = message or get_error_message("RESOURCE_NOT_FOUND", "Resource not found")
        super().__init__("RESOURCE_NOT_FOUND", msg, 404)


def register_error_handlers(app) -> None:
    """Register error handlers for the Flask app."""

    @app.errorhandler(APIError)
    def handle_api_error(error: APIError):
        response = {
            "error": {
                "code": error.code,
                "message": error.message,
                "details": error.details if error.details else None,
            },
        }
        # Remove details if empty
        if not response["error"]["details"]:
            response["error"].pop("details")
        return jsonify(response), error.status_code

    @app.errorhandler(HTTPException)
    def handle_http_exception(error: HTTPException):
        code = f"HTTP_{error.code}_{error.name.upper().replace(' ', '_')}"
        message = error.description
        response = {
            "error": {
                "code": code,
                "message": message,
            },
        }
        return jsonify(response), error.code

    @app.errorhandler(Exception)
    def handle_unexpected_error(error: Exception):
        # Log the error here if needed
        code = "GENERIC_ERROR"
        message = get_error_message(code, "An unexpected error occurred")
        response = {
            "error": {
                "code": code,
                "message": message,
            },
        }
        return jsonify(response), 500
