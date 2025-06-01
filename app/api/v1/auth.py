from typing import Literal

from flask import Blueprint, jsonify, request
from flask.wrappers import Response
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt_identity,
    verify_jwt_in_request,
)

from app.constants import ErrorMessages
from app.services.auth_service import AuthService

auth_bp = Blueprint("auth", __name__, url_prefix="/api/v1/auth")
auth_service = AuthService()


@auth_bp.route("/login", methods=["POST"])
def login() -> tuple[Response, Literal]:
    """User login endpoint."""
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    user = auth_service.authenticate(email, password)
    if not user:
        return (
            jsonify(
                {"error": {"code": 401, "message": ErrorMessages.INVALID_CREDENTIALS}},
            ),
            401,
        )

    # identityを文字列に変換
    access_token = create_access_token(identity=str(user.user_id))
    refresh_token = create_refresh_token(identity=str(user.user_id))

    return (
        jsonify(
            {
                "token": access_token,
                "refresh_token": refresh_token,
                "user": {
                    "id": user.user_id,
                    "username": user.username,
                    "email": user.email,
                },
            },
        ),
        200,
    )


@auth_bp.route("/register", methods=["POST"])
def register() -> tuple[Response, Literal]:
    """User registration endpoint."""
    data = request.get_json()
    try:
        user = auth_service.register_user(data)
    except ValueError as e:
        return jsonify({"error": {"code": 400, "message": str(e)}}), 400

    # identityを文字列に変換
    access_token = create_access_token(identity=str(user.user_id))
    refresh_token = create_refresh_token(identity=str(user.user_id))

    return (
        jsonify(
            {
                "token": access_token,
                "refresh_token": refresh_token,
                "user": {
                    "id": user.user_id,
                    "username": user.username,
                    "email": user.email,
                },
            },
        ),
        201,
    )


@auth_bp.route("/refresh", methods=["POST"])
def refresh_token() -> tuple[Response, Literal]:
    """Refresh access token using refresh token."""
    try:
        # リフレッシュトークンの検証
        verify_jwt_in_request(refresh=True)
        current_user = get_jwt_identity()

        # 新しいトークンを生成
        access_token = create_access_token(identity=current_user)
        refresh_token = create_refresh_token(identity=current_user)

        return (
            jsonify(
                {
                    "data": {
                        "access_token": access_token,
                        "refresh_token": refresh_token,
                    },
                },
            ),
            200,
        )
    except Exception as e:
        error_message = str(e)

        # エラーの種類に応じて適切なレスポンスを返す
        if "expired" in error_message.lower():
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
        if (
            "missing" in error_message.lower()
            or "authorization" in error_message.lower()
        ):
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
        # その他のエラー
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
