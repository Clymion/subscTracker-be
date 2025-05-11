import pytest
from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException

from app.common.errors import (
    APIError,
    AuthenticationError,
    ResourceNotFoundError,
    ValidationError,
    register_error_handlers,
)


@pytest.fixture
def app():
    app = Flask(__name__)

    @app.route("/raise-validation-error")
    def raise_validation_error():
        raise ValidationError("Invalid input", field="email", reason="Invalid format")

    @app.route("/raise-auth-error")
    def raise_auth_error():
        raise AuthenticationError("Invalid token")

    @app.route("/raise-not-found-error")
    def raise_not_found_error():
        raise ResourceNotFoundError("User not found")

    @app.route("/raise-generic-api-error")
    def raise_generic_api_error():
        raise APIError("GENERIC_ERROR", "A generic error occurred")

    register_error_handlers(app)
    return app


@pytest.fixture
def client(app):
    return app.test_client()


def test_validation_error(client):
    response = client.get("/raise-validation-error")
    assert response.status_code == 400
    data = response.get_json()
    assert data["error"]["code"] == "VALIDATION_ERROR"
    assert "Invalid input" in data["error"]["message"]
    assert "field" in data["error"]["details"]
    assert "reason" in data["error"]["details"]


def test_authentication_error(client):
    response = client.get("/raise-auth-error")
    assert response.status_code == 401
    data = response.get_json()
    assert data["error"]["code"] == "AUTHENTICATION_ERROR"
    assert "Invalid token" in data["error"]["message"]


def test_resource_not_found_error(client):
    response = client.get("/raise-not-found-error")
    assert response.status_code == 404
    data = response.get_json()
    assert data["error"]["code"] == "RESOURCE_NOT_FOUND"
    assert "User not found" in data["error"]["message"]


def test_generic_api_error(client):
    response = client.get("/raise-generic-api-error")
    assert response.status_code == 500
    data = response.get_json()
    assert data["error"]["code"] == "GENERIC_ERROR"
    assert "A generic error occurred" in data["error"]["message"]


def test_unhandled_http_exception(client):
    @client.application.route("/raise-http-exception")
    def raise_http_exception():
        from werkzeug.exceptions import Forbidden

        raise Forbidden("Forbidden access")

    response = client.get("/raise-http-exception")
    assert response.status_code == 403
    data = response.get_json()
    assert data["error"]["code"] == "HTTP_403_FORBIDDEN"
    assert "Forbidden access" in data["error"]["message"]
