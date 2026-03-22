"""
ユーザープロフィールAPIのエンドポイントを定義するモジュール
"""

from flask import Blueprint, jsonify, request
from flask.wrappers import Response
from flask_jwt_extended import get_jwt_identity

from app.common.auth_middleware import jwt_required_custom
from app.common.logging_setup import get_logger
from app.common.response_utils import success_response
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
