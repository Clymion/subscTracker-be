"""
Label APIのエンドポイントを定義するモジュール

このファイルでは、ラベルのCRUD操作に関連する
RESTful APIエンドポイントをFlask Blueprintを使って作成する
"""

from flask import Blueprint, jsonify, request
from flask.wrappers import Response
from flask_jwt_extended import get_jwt_identity

from app.common.auth_middleware import jwt_required_custom
from app.exceptions import (
    DuplicateLabelError,
    LabelHierarchyError,
    LabelNotFoundError,
    ValidationError,
)
from app.models import db
from app.services.label_service import LabelService

# ラベル用のBlueprintを作成
label_bp = Blueprint("label", __name__)
# データベースセッションを渡してサービスを初期化
label_service = LabelService(session=db.session)


@label_bp.route("/labels", methods=["GET"])
@jwt_required_custom
def get_labels() -> tuple[Response, int]:
    """認証済みユーザーのラベル一覧を取得する"""
    user_id = get_jwt_identity()

    # parent_idパラメータの処理
    parent_id_param = request.args.get("parent_id")
    parent_id = None
    # parent_idがないラベルを指定するためのフラグ
    filter_root_labels = False

    if parent_id_param is not None:
        if parent_id_param == "null":
            # "null"文字列の場合はNoneとして扱う(ルートレベルのラベル)
            filter_root_labels = True
        else:
            try:
                # 数値への変換を試行
                parent_id = int(parent_id_param)
            except ValueError:
                # 無効なparent_id値の場合は400エラー
                return (
                    jsonify(
                        {
                            "error": {
                                "code": 400,
                                "message": "Invalid parent_id parameter. Must be an integer or 'null'.",
                            },
                        },
                    ),
                    400,
                )

    # サービスを呼び出して、使用回数を含むラベルリストを取得
    labels_with_usage = label_service.get_labels_by_user_with_usage(
        int(user_id),
        parent_id=parent_id,
        filter_root_labels=filter_root_labels,
    )

    response_data = {
        "data": {
            "labels": labels_with_usage,
        },
        "meta": {"total": len(labels_with_usage)},
    }
    return jsonify(response_data), 200


@label_bp.route("/labels", methods=["POST"])
@jwt_required_custom
def create_label() -> tuple[Response, int]:
    """新しいラベルを作成する"""
    user_id = get_jwt_identity()
    data = request.get_json()

    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    try:
        new_label = label_service.create_label(user_id=int(user_id), data=data)
        # 作成成功時は、使用回数も含めたデータを返す
        response_data = label_service.get_label_with_usage(
            user_id=int(user_id),
            label_id=new_label.label_id,
        )
        return jsonify({"data": response_data}), 201
    except (DuplicateLabelError, LabelHierarchyError, ValidationError) as e:
        return jsonify({"error": {"code": 400, "message": str(e)}}), 400
    except Exception as e:
        # 予期せぬエラー
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


@label_bp.route("/labels/<int:label_id>", methods=["GET"])
@jwt_required_custom
def get_label_by_id(label_id: int) -> tuple[Response, int]:
    """指定されたIDのラベル詳細を取得する"""
    user_id = get_jwt_identity()
    try:
        label_with_usage = label_service.get_label_with_usage(
            user_id=int(user_id),
            label_id=label_id,
        )
        return jsonify({"data": label_with_usage}), 200
    except LabelNotFoundError as e:
        return jsonify({"error": {"code": 404, "message": str(e)}}), 404


@label_bp.route("/labels/<int:label_id>", methods=["PUT"])
@jwt_required_custom
def update_label(label_id: int) -> tuple[Response, int]:
    """指定されたIDのラベルを更新する"""
    user_id = get_jwt_identity()
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    try:
        label_service.update_label(user_id=int(user_id), label_id=label_id, data=data)
        # 更新成功後、最新のデータを取得して返す
        updated_label_data = label_service.get_label_with_usage(
            user_id=int(user_id),
            label_id=label_id,
        )
        return jsonify({"data": updated_label_data}), 200
    except LabelNotFoundError as e:
        return jsonify({"error": {"code": 404, "message": str(e)}}), 404
    except (DuplicateLabelError, LabelHierarchyError, ValidationError) as e:
        return jsonify({"error": {"code": 400, "message": str(e)}}), 400


@label_bp.route("/labels/<int:label_id>", methods=["DELETE"])
@jwt_required_custom
def delete_label(label_id: int) -> tuple[Response, int]:
    """指定されたIDのラベルを削除する"""
    user_id = get_jwt_identity()
    try:
        label_service.delete_label(user_id=int(user_id), label_id=label_id)
        return "", 204
    except LabelNotFoundError as e:
        return jsonify({"error": {"code": 404, "message": str(e)}}), 404
    except ValidationError as e:
        return jsonify({"error": {"code": 400, "message": str(e)}}), 400
