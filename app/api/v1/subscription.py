"""
Subscription APIのエンドポイントを定義するモジュールなのだ。

このファイルでは、サブスクリプションのCRUD操作に関連する
RESTful APIエンドポイントをFlask Blueprintを使って作成するのだ。
"""

from datetime import datetime

from flask import Blueprint, jsonify, request
from flask.wrappers import Response
from flask_jwt_extended import get_jwt_identity

from app.common.auth_middleware import jwt_required_custom
from app.exceptions import (
    DuplicateSubscriptionError,
    SubscriptionAccessDenied,
    SubscriptionNotFoundError,
    ValidationError,
)
from app.models import db
from app.services.subscription_service import SubscriptionService

# サブスクリプション用のBlueprintを作成
subscription_bp = Blueprint("subscription", __name__)
# データベースセッションを渡してサービスを初期化
subscription_service = SubscriptionService(session=db.session)


@subscription_bp.route("/subscriptions", methods=["GET"])
@jwt_required_custom
def get_subscriptions() -> tuple[Response, int]:
    """認証済みユーザーのサブスクリプション一覧を取得するのだ。"""
    user_id = get_jwt_identity()

    # 現時点では、フィルタリングやソート、ページネーションは実装しない
    # TDDの次のサイクルで追加していくのだ
    subscriptions = subscription_service.get_subscriptions_by_user(user_id=int(user_id))

    # レスポンスデータを構築
    response_data = {
        "data": {
            "subscriptions": [sub.to_dict() for sub in subscriptions],
        },
        "meta": {"total": len(subscriptions)},
    }
    return jsonify(response_data), 200


@subscription_bp.route("/subscriptions", methods=["POST"])
@jwt_required_custom
def create_subscription() -> tuple[Response, int]:
    """新しいサブスクリプションを作成するのだ。"""
    user_id = get_jwt_identity()
    data = request.get_json()

    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    # 日付文字列をdateオブジェクトに変換
    if "initial_payment_date" in data and isinstance(data["initial_payment_date"], str):
        try:
            data["initial_payment_date"] = datetime.fromisoformat(
                data["initial_payment_date"],
            ).date()
        except (ValueError, TypeError):
            return (
                jsonify(
                    {
                        "error": {
                            "code": 400,
                            "message": "Invalid date format for initial_payment_date",
                        },
                    },
                ),
                400,
            )

    try:
        # サービスレイヤーを呼び出してサブスクリプションを作成
        new_subscription = subscription_service.create_subscription(
            user_id=int(user_id),
            data=data,
        )
        return (
            jsonify({"data": new_subscription.to_dict()}),
            201,
        )
    except DuplicateSubscriptionError as e:
        return jsonify({"error": {"code": 400, "message": str(e)}}), 400
    except ValidationError as e:
        return jsonify({"error": {"code": 400, "message": str(e)}}), 400
    except Exception as e:
        # 予期せぬエラーは500を返す
        return (
            jsonify(
                {
                    "error": {
                        "code": 500,
                        "message": f"An unexpected error occurred: {e}",
                    },
                },
            ),
            500,
        )


@subscription_bp.route("/subscriptions/<int:subscription_id>", methods=["GET"])
@jwt_required_custom
def get_subscription_by_id(subscription_id: int) -> tuple[Response, int]:
    """指定されたIDのサブスクリプション詳細を取得するのだ。"""
    user_id = get_jwt_identity()
    try:
        subscription = subscription_service.get_subscription(
            user_id=int(user_id), subscription_id=subscription_id,
        )
        return jsonify({"data": subscription.to_dict()}), 200
    except SubscriptionNotFoundError as e:
        return jsonify({"error": {"code": 404, "message": str(e)}}), 404
    except SubscriptionAccessDenied as e:
        return jsonify({"error": {"code": 403, "message": str(e)}}), 403


@subscription_bp.route("/subscriptions/<int:subscription_id>", methods=["PUT"])
@jwt_required_custom
def update_subscription(subscription_id: int) -> tuple[Response, int]:
    """指定されたIDのサブスクリプションを更新するのだ。"""
    user_id = get_jwt_identity()
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    try:
        updated_subscription = subscription_service.update_subscription(
            user_id=int(user_id), subscription_id=subscription_id, data=data,
        )
        return jsonify({"data": updated_subscription.to_dict()}), 200
    except SubscriptionNotFoundError as e:
        return jsonify({"error": {"code": 404, "message": str(e)}}), 404
    except SubscriptionAccessDenied as e:
        return jsonify({"error": {"code": 403, "message": str(e)}}), 403
    except (DuplicateSubscriptionError, ValidationError) as e:
        return jsonify({"error": {"code": 400, "message": str(e)}}), 400


@subscription_bp.route("/subscriptions/<int:subscription_id>", methods=["DELETE"])
@jwt_required_custom
def delete_subscription(subscription_id: int) -> tuple[Response, int]:
    """指定されたIDのサブスクリプションを削除するのだ。"""
    user_id = get_jwt_identity()
    try:
        subscription_service.delete_subscription(
            user_id=int(user_id), subscription_id=subscription_id,
        )
        return "", 204
    except SubscriptionNotFoundError as e:
        return jsonify({"error": {"code": 404, "message": str(e)}}), 404
    except SubscriptionAccessDenied as e:
        return jsonify({"error": {"code": 403, "message": str(e)}}), 403
