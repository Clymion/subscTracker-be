from typing import Literal, NoReturn

import pytest
from flask import Flask, jsonify
from flask.testing import FlaskClient
from flask.wrappers import Response
from flask_jwt_extended import JWTManager, create_access_token, create_refresh_token
from werkzeug.exceptions import Forbidden

from app.common.auth_middleware import jwt_required_custom, permission_required
from app.constants import ErrorMessages


@pytest.fixture
def app() -> Flask:
    """Create a Flask app with JWT configuration for testing."""
    app = Flask(__name__)
    app.config["JWT_SECRET_KEY"] = "test-secret-key"
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = 3600
    app.config["JWT_REFRESH_TOKEN_EXPIRES"] = 2592000
    JWTManager(app)

    @app.route("/protected")
    @jwt_required_custom
    def protected() -> tuple[Response, Literal[200]]:
        return jsonify(message="Access granted"), 200

    @app.route("/admin")
    @jwt_required_custom
    @permission_required(lambda identity: False)  # Simulate permission check failure
    def admin() -> NoReturn:
        raise Forbidden(ErrorMessages.INSUFFICIENT_PERMISSIONS)

    return app


@pytest.fixture
def client(app: Flask) -> FlaskClient:
    return app.test_client()


def test_valid_jwt_allows_access(client: FlaskClient, app: Flask) -> None:
    with app.app_context():
        access_token = create_access_token(identity="user1")
    response = client.get(
        "/protected",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 200
    assert response.get_json() == {"message": "Access granted"}


def test_missing_jwt_returns_401(client: FlaskClient) -> None:
    response = client.get("/protected")
    assert response.status_code == 401
    data = response.get_json()
    assert data["error"]["code"] == 401
    assert (
        "Unauthorized" in data["error"]["message"]
        or "authorization" in data["error"]["message"].lower()
    )


def test_expired_jwt_returns_401(
    client: FlaskClient,
    monkeypatch: FlaskClient,
    app: Flask,
) -> None:
    # Patch the verify_jwt_in_request to simulate expired token error
    from flask_jwt_extended.exceptions import JWTDecodeError

    def raise_expired() -> None:
        msg = "Token has expired"
        raise JWTDecodeError(msg)

    monkeypatch.setattr(
        "flask_jwt_extended.view_decorators._decode_jwt_from_request",
        raise_expired,
    )

    with app.app_context():
        access_token = create_access_token(identity="user1")
    response = client.get(
        "/protected",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 401
    data = response.get_json()
    assert data["error"]["code"] == 401
    assert ErrorMessages.TOKEN_EXPIRED in data["error"]["message"]


def test_malformed_jwt_returns_401(client: FlaskClient) -> None:
    malformed_token = "this.is.not.a.valid.token"
    response = client.get(
        "/protected",
        headers={"Authorization": f"Bearer {malformed_token}"},
    )
    assert response.status_code == 401
    data = response.get_json()
    assert data["error"]["code"] == 401


def test_refresh_token_validation_success(client: FlaskClient, app: Flask) -> None:
    with app.app_context():
        refresh_token = create_refresh_token(identity="user1")
    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
        headers={"Authorization": f"Bearer {refresh_token}"},
    )
    assert response.status_code == 404


def test_refresh_token_expired_or_invalid_returns_401(
    client: FlaskClient,
    monkeypatch: FlaskClient,
    app: Flask,
) -> None:
    from flask_jwt_extended.exceptions import RevokedTokenError

    def raise_revoked() -> None:
        msg = "Token revoked"
        raise RevokedTokenError(msg)

    monkeypatch.setattr(
        "flask_jwt_extended.view_decorators._decode_jwt_from_request", raise_revoked,
    )

    with app.app_context():
        refresh_token = create_refresh_token(identity="user1")
    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
        headers={"Authorization": f"Bearer {refresh_token}"},
    )
    assert response.status_code == 404


def test_user_with_sufficient_permissions_can_access(
    client: FlaskClient,
    app: Flask,
) -> None:
    with app.app_context():
        access_token = create_access_token(identity="user1")
    response = client.get(
        "/protected", headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 200


def test_user_without_permissions_receives_403(client: FlaskClient, app: Flask) -> None:
    with app.app_context():
        access_token = create_access_token(identity="user1")
    response = client.get("/admin", headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == 403
    data = response.get_json()
    assert data["error"]["code"] == 403
    assert ErrorMessages.INSUFFICIENT_PERMISSIONS in data["error"]["message"]
