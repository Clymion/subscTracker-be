from functools import wraps
from typing import Any, Callable

from flask import jsonify
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request

from app.constants import ErrorMessages


def jwt_required_custom(fn: Callable[..., Any]) -> Callable[..., Any]:
    """
    Custom decorator to verify JWT in request and handle errors with consistent JSON responses.

    Args:
        fn: The route handler function to decorate.

    Returns:
        The decorated function with JWT verification.

    """

    @wraps(fn)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            verify_jwt_in_request()
        except Exception as e:
            message = str(e)
            if "expired" in message.lower():
                return (
                    jsonify(
                        {
                            "error": {
                                "code": 401,
                                "name": "Unauthorized",
                                "message": ErrorMessages.TOKEN_EXPIRED,
                            },
                        },
                    ),
                    401,
                )
            # Adjusted error message for missing token to match test expectations
            if "missing" in message.lower() or "authorization" in message.lower():
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
        return fn(*args, **kwargs)

    return wrapper


def permission_required(
    permission_check: Callable[[str | None], bool],
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    Check user permissions with decorator.

    Args:
        permission_check: A callable that takes user identity and returns True if permitted.

    Raises:
        403 Forbidden if permission check fails.

    Returns:
        A decorator that applies the permission check to a route handler.

    """

    def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            identity = get_jwt_identity()
            if not permission_check(identity):
                return (
                    jsonify(
                        {
                            "error": {
                                "code": 403,
                                "name": "Forbidden",
                                "message": ErrorMessages.INSUFFICIENT_PERMISSIONS,
                            },
                        },
                    ),
                    403,
                )
            return fn(*args, **kwargs)

        return wrapper

    return decorator
