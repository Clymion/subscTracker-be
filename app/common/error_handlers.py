from flask import Flask, jsonify
from werkzeug.exceptions import (
    BadRequest,
    Forbidden,
    HTTPException,
    InternalServerError,
    NotFound,
    Unauthorized,
)

from app.constants import ErrorMessages


def register_error_handlers(app: Flask) -> None:
    """
    Register common error handlers for the Flask app.

    Args:
        app: The Flask application instance.

    """

    @app.errorhandler(HTTPException)
    def handle_http_exception(e: HTTPException) -> tuple:
        """
        Handle HTTP exceptions and return JSON response.

        Args:
            e: The HTTPException instance.

        Returns:
            A tuple of JSON response and HTTP status code.

        """
        response = e.get_response()
        response.data = jsonify(
            {
                "error": {
                    "code": e.code,
                    "name": e.name,
                    "message": e.description or ErrorMessages.BAD_REQUEST,
                },
            },
        ).data
        response.content_type = "application/json"
        return response

    @app.errorhandler(400)
    @app.errorhandler(BadRequest)
    def bad_request_error(e: HTTPException | Exception) -> tuple:
        """Handle 400 Bad Request errors."""
        return (
            jsonify(
                {
                    "error": {
                        "code": 400,
                        "name": "Bad Request",
                        "message": ErrorMessages.BAD_REQUEST,
                    },
                },
            ),
            400,
        )

    @app.errorhandler(401)
    @app.errorhandler(Unauthorized)
    def unauthorized_error(e: HTTPException | Exception) -> tuple:
        """Handle 401 Unauthorized errors."""
        return (
            jsonify(
                {
                    "error": {
                        "code": 401,
                        "name": "Unauthorized",
                        "message": ErrorMessages.UNAUTHORIZED,
                    },
                },
            ),
            401,
        )

    @app.errorhandler(403)
    @app.errorhandler(Forbidden)
    def forbidden_error(e: HTTPException | Exception) -> tuple:
        """Handle 403 Forbidden errors."""
        return (
            jsonify(
                {
                    "error": {
                        "code": 403,
                        "name": "Forbidden",
                        "message": ErrorMessages.FORBIDDEN,
                    },
                },
            ),
            403,
        )

    @app.errorhandler(404)
    @app.errorhandler(NotFound)
    def not_found_error(e: HTTPException) -> tuple:
        """Handle 404 Not Found errors."""
        return (
            jsonify(
                {
                    "error": {
                        "code": 404,
                        "name": "Not Found",
                        "message": ErrorMessages.NOT_FOUND,
                    },
                },
            ),
            404,
        )

    @app.errorhandler(Exception)
    @app.errorhandler(InternalServerError)
    def internal_server_error(e: HTTPException | Exception) -> tuple:
        """Handle unexpected server errors."""
        # Log the exception here if logging is set up
        return (
            jsonify(
                {
                    "error": {
                        "code": 500,
                        "name": "Internal Server Error",
                        "message": "An unexpected error occurred.",
                    },
                },
            ),
            500,
        )
