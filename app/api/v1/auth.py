from flask import Blueprint, jsonify, request
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt_identity,
    jwt_required,
)

from app.constants import ErrorMessages
from app.services.auth_service import AuthService

auth_bp = Blueprint("auth", __name__, url_prefix="/api/v1/auth")
auth_service = AuthService()

@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    user = auth_service.authenticate(email, password)
    if not user:
        return (
            jsonify(
                {"error": {"code": 401, "message": ErrorMessages.INVALID_CREDENTIALS}}
            ),
            401,
        )

    access_token = create_access_token(identity=user.user_id)
    refresh_token = create_refresh_token(identity=user.user_id)

    return (
        jsonify(
            {
                "token": access_token,
                "refresh_token": refresh_token,
                "user": {"id": user.user_id, "username": user.username, "email": user.email},
            }
        ),
        200,
    )

@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    try:
        user = auth_service.register_user(data)
    except ValueError as e:
        return jsonify({"error": {"code": 400, "message": str(e)}}), 400

    access_token = create_access_token(identity=user.user_id)
    refresh_token = create_refresh_token(identity=user.user_id)

    return (
        jsonify(
            {
                "token": access_token,
                "refresh_token": refresh_token,
                "user": {"id": user.user_id, "username": user.username, "email": user.email},
            }
        ),
        201,
    )

@auth_bp.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh_token():
    current_user = get_jwt_identity()
    access_token = create_access_token(identity=current_user)
    refresh_token = create_refresh_token(identity=current_user)
    return (
        jsonify(
            {"data": {"access_token": access_token, "refresh_token": refresh_token}}
        ),
        200,
    )
