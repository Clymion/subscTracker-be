import pytest
from flask import Flask, jsonify
from flask_jwt_extended import create_access_token
from app.common.auth_middleware import jwt_required_custom, permission_required
from app.models import db
from app.models.user import User

@pytest.fixture
def app_wrapper(request, app):
    # Use the app fixture from tests/common/conftest.py and extend it
    app.config["JWT_SECRET_KEY"] = "test-secret"
    app.config["TESTING"] = True

    with app.app_context():
        db.create_all()
        user = User(username="testuser", email="test@example.com")
        user.set_password("password")
        db.session.add(user)
        db.session.commit()

    @app.route("/protected")
    @jwt_required_custom
    def protected():
        return jsonify(message="Access granted")

    @app.route("/permission")
    @jwt_required_custom
    @permission_required(lambda identity: identity == "allowed_user")
    def permission_route():
        return jsonify(message="Permission granted")

    yield app

@pytest.fixture
def client(app_wrapper):
    return app_wrapper.test_client()

def test_jwt_required_custom_allows_access(client):
    token = create_access_token(identity="testuser")
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/protected", headers=headers)
    assert response.status_code == 200
    assert response.get_json()["message"] == "Access granted"

def test_jwt_required_custom_denies_access(client):
    response = client.get("/protected")
    assert response.status_code == 401

def test_permission_required_allows(client):
    token = create_access_token(identity="allowed_user")
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/permission", headers=headers)
    assert response.status_code == 200
    assert response.get_json()["message"] == "Permission granted"

def test_permission_required_denies(client):
    token = create_access_token(identity="denied_user")
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/permission", headers=headers)
    assert response.status_code == 403
