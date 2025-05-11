from flask import Blueprint, Response, jsonify

bp = Blueprint("v1", __name__)

@bp.route("/test")
def test() -> Response:
    """
    Test endpoint for API v1.

    Returns a simple JSON response to verify the API is working.
    """
    return jsonify({"message": "API v1 test endpoint"})


@bp.route("/health")
def health_check() -> Response:
    """
    Health check endpoint for API v1.

    Returns a JSON response indicating the API is healthy.
    """
    return jsonify({"status": "ok"})
