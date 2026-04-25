"""
ユーザープロフィールAPIのエンドポイントを定義するモジュール
"""

from flask import Blueprint, jsonify, request
from flask.wrappers import Response
from flask_jwt_extended import get_jwt_identity

from app.common.auth_middleware import jwt_required_custom
from app.common.logging_setup import get_logger
from app.common.response_utils import success_response
from app.constants import ErrorMessages
from app.exceptions import InvalidPasswordError, UserNotFoundError
from app.models import db
from app.services.user_service import UserService

logger = get_logger(__name__)

user_bp = Blueprint("user", __name__)
user_service = UserService(session=db.session)


@user_bp.route("/users/<int:user_id>", methods=["GET"])
@jwt_required_custom
def get_user(user_id: int) -> tuple[Response, int]:
    """ユーザープロフィールを取得する"""
    current_user_id = get_jwt_identity()

    # ユーザーの存在確認を先に行う（要件1.4）
    user = user_service.get_user_by_id(user_id)
    if not user:
        return (
            jsonify({"error": {"code": 404, "message": "ユーザーが見つかりません"}}),
            404,
        )

    # 自分のプロフィールのみ取得可能
    if int(current_user_id) != user_id:
        return (
            jsonify(
                {"error": {"code": 403, "message": "他のユーザーのプロフィールは取得できません"}},
            ),
            403,
        )

    return success_response({
        "id": str(user.user_id),
        "username": user.username,
        "email": user.email,
        "base_currency": user.base_currency,
        "created_at": user.created_at.isoformat(),
    })


@user_bp.route("/users/<int:user_id>", methods=["PATCH"])
@jwt_required_custom
def update_user(user_id: int) -> tuple[Response, int]:
    """ユーザープロフィールを更新する"""
    current_user_id = get_jwt_identity()

    # 自分のプロフィールのみ更新可能
    if int(current_user_id) != user_id:
        return (
            jsonify(
                {"error": {"code": 403, "message": "他のユーザーのプロフィールは更新できません"}},
            ),
            403,
        )

    data = request.get_json()
    if data is None:
        return jsonify({"error": {"code": 400, "message": "Invalid JSON"}}), 400

    # 空のJSONオブジェクトの検証
    if not data:
        return jsonify({"error": {"code": 400, "message": "更新するフィールドがありません"}}), 400

    try:
        user = user_service.update_user(user_id, data)
    except ValueError as e:
        return jsonify({"error": {"code": 400, "message": str(e)}}), 400

    return success_response({
        "id": str(user.user_id),
        "username": user.username,
        "email": user.email,
        "base_currency": user.base_currency,
        "created_at": user.created_at.isoformat(),
    })


@user_bp.route("/users/<int:user_id>", methods=["DELETE"])
@jwt_required_custom
def delete_user(user_id: int) -> tuple[Response, int]:
    """
    ユーザーアカウントを削除する。

    Args:
        user_id: 削除対象のユーザーID

    Returns:
        204 No Content on success
        400 Bad Request for validation errors
        403 Forbidden for authorization errors
        404 Not Found if user doesn't exist
        500 Internal Server Error for unexpected errors
    """
    current_user_id = get_jwt_identity()

    # 自分のアカウントのみ削除可能
    if int(current_user_id) != user_id:
        logger.warning(
            f"Delete attempt denied: user {current_user_id} tried to delete user {user_id}"
        )
        return (
            jsonify(
                {"error": {"code": 403, "message": ErrorMessages.CANNOT_DELETE_OTHER_USER}},
            ),
            403,
        )

    data = request.get_json()
    if data is None or "password" not in data:
        return (
            jsonify({"error": {"code": 400, "message": ErrorMessages.PASSWORD_REQUIRED}}),
            400,
        )

    password = data.get("password")
    if not password:
        return (
            jsonify({"error": {"code": 400, "message": ErrorMessages.PASSWORD_REQUIRED}}),
            400,
        )

    try:
        user_service.delete_user(user_id, password)
        return "", 204
    except UserNotFoundError:
        return (
            jsonify({"error": {"code": 404, "message": "ユーザーが見つかりません"}}),
            404,
        )
    except InvalidPasswordError:
        return (
            jsonify({"error": {"code": 400, "message": ErrorMessages.INVALID_PASSWORD}}),
            400,
        )
    except Exception as e:
        logger.exception(f"Unexpected error during user deletion: {e}")
        return (
            jsonify({"error": {"code": 500, "message": "Internal server error"}}),
            500,
        )


@user_bp.route("/users/<int:user_id>/change-password", methods=["POST"])
@jwt_required_custom
def change_password(user_id: int) -> tuple[Response, int]:
    """
    ユーザーのパスワードを変更する。

    Args:
        user_id: パスワード変更対象のユーザーID

    Returns:
        200 OK on success
        400 Bad Request for validation errors
        401 Unauthorized for authentication errors
        403 Forbidden for authorization errors
        404 Not Found if user doesn't exist
        500 Internal Server Error for unexpected errors
    """
    current_user_id = get_jwt_identity()

    # 自分のパスワードのみ変更可能
    if int(current_user_id) != user_id:
        logger.warning(
            f"Password change denied: user {current_user_id} tried to change user {user_id}"
        )
        return (
            jsonify(
                {
                    "error": {
                        "code": 403,
                        "message": "他のユーザーのパスワードは変更できません",
                    }
                }
            ),
            403,
        )

    data = request.get_json()
    if data is None:
        return (
            jsonify({"error": {"code": 400, "message": "Invalid JSON"}}),
            400,
        )

    # 必須フィールドのバリデーション
    if "current_password" not in data or not data["current_password"]:
        return (
            jsonify(
                {"error": {"code": 400, "message": "現在のパスワードが必要です"}}
            ),
            400,
        )

    if "new_password" not in data or not data["new_password"]:
        return (
            jsonify(
                {"error": {"code": 400, "message": "新しいパスワードが必要です"}}
            ),
            400,
        )

    current_password = data["current_password"]
    new_password = data["new_password"]

    try:
        user_service.change_password(user_id, current_password, new_password)
        return success_response({"message": "パスワードが正常に変更されました"})
    except UserNotFoundError:
        return (
            jsonify({"error": {"code": 404, "message": "ユーザーが見つかりません"}}),
            404,
        )
    except InvalidPasswordError:
        return (
            jsonify(
                {
                    "error": {
                        "code": 400,
                        "message": "現在のパスワードが正しくありません",
                    }
                }
            ),
            400,
        )
    except ValueError as e:
        return jsonify({"error": {"code": 400, "message": str(e)}}), 400
    except Exception as e:
        logger.exception(f"Unexpected error during password change: {e}")
        return (
            jsonify({"error": {"code": 500, "message": "Internal server error"}}),
            500,
        )
