"""Payment History APIエンドポイント."""


from flask import Blueprint, Response, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from marshmallow import Schema, fields, validate
from marshmallow import ValidationError as MarshmallowValidationError

from app.exceptions import (
    BadRequestError,
    ForbiddenError,
    ResourceNotFoundError,
    ValidationError,
)
from app.models import db
from app.models.payment_history import PaymentHistory
from app.repositories.exchange_rate_repository import ExchangeRateRepository
from app.repositories.payment_history_repository import PaymentHistoryRepository
from app.repositories.subscription_repository import SubscriptionRepository
from app.repositories.user_repository import UserRepository
from app.services.exchange_rate_service import ExchangeRateService
from app.services.payment_history_service import PaymentHistoryService

payment_history_bp = Blueprint("payment_history_bp", __name__)


# Instantiate repositories
payment_history_repository = PaymentHistoryRepository(session=db.session)
user_repository = UserRepository(session=db.session)
subscription_repository = SubscriptionRepository(session=db.session)
exchange_rate_repository = ExchangeRateRepository(session=db.session)

# Instantiate services
exchange_rate_service = ExchangeRateService(
    exchange_rate_repository=exchange_rate_repository,
)

# Instantiate service with injected repositories
payment_history_service = PaymentHistoryService(
    session=db.session,
    payment_history_repository=payment_history_repository,
    user_repository=user_repository,
    subscription_repository=subscription_repository,
    exchange_rate_service=exchange_rate_service,
)


class PaymentCreateRequestSchema(Schema):
    """支払履歴登録リクエストのスキーマ."""

    subscription_id = fields.Int(required=True)
    payment_date = fields.Date(required=True)
    amount = fields.Float(required=True, validate=validate.Range(min=0.01))
    currency = fields.Str(required=True, validate=validate.Length(equal=3))
    payment_method = fields.Str(required=True)


class PaymentUpdateRequestSchema(Schema):
    """支払履歴更新リクエストのスキーマ."""

    subscription_id = fields.Int(required=False)
    payment_date = fields.Date(required=False)
    amount = fields.Float(required=False, validate=validate.Range(min=0.01))
    currency = fields.Str(required=False, validate=validate.Length(equal=3))
    payment_method = fields.Str(required=False)


@payment_history_bp.route("/payments", methods=["GET"])
@jwt_required()
def get_payment_histories() -> Response:
    """支払履歴一覧を取得する."""
    user_id = get_jwt_identity()
    args = request.args

    try:
        filters = {
            "subscription_id": args.get("subscription_id", type=int),
            "start_date": args.get("start_date"),
            "end_date": args.get("end_date"),
            "payment_method": args.get("payment_method"),
            "currency": args.get("currency"),
        }

        sort_by = args.get("sort_by", default="payment_date")
        if sort_by not in PaymentHistory.__table__.columns:
            msg = f"Invalid sort_by column: {sort_by}"
            raise ValueError(msg)

        sort_order = args.get("sort_order", default="desc")
        limit = args.get("limit", default=100, type=int)
        offset = args.get("offset", default=0, type=int)

        histories, total = payment_history_service.get_payment_history(
            user_id=user_id,
            filters=filters,
            sort_by=sort_by,
            sort_order=sort_order,
            limit=limit,
            offset=offset,
        )

        response_data = {
            "data": {"payments": [h.to_dict() for h in histories]},
            "meta": {"total": total},
        }

        return jsonify(response_data)

    except ValueError as e:
        return jsonify({"error": {"code": 400, "message": str(e)}}), 400


@payment_history_bp.route("/payments", methods=["POST"])
@jwt_required()
def create_payment() -> Response:
    """新しい支払履歴を登録する."""
    user_id = get_jwt_identity()
    json_data = request.get_json()
    if not json_data:
        msg = "Request body is empty"
        raise BadRequestError(msg)

    try:
        # Marshmallow validation
        payment_data = PaymentCreateRequestSchema().load(json_data)

        # Service call
        created_payment = payment_history_service.create_payment(
            user_id=user_id, payment_data=payment_data,
        )

        return jsonify({"data": created_payment.to_dict()}), 201

    except ResourceNotFoundError as e:
        return jsonify({"error": {"code": 404, "message": str(e)}}), 404
    except ForbiddenError as e:
        return jsonify({"error": {"code": 403, "message": str(e)}}), 403
    except ValidationError as e:
        return jsonify({"error": {"code": 400, "message": str(e)}}), 400
    except MarshmallowValidationError as e:
        return jsonify({"error": {"code": 400, "message": e.messages}}), 400


@payment_history_bp.route("/payments/<int:payment_id>", methods=["PATCH"])
@jwt_required()
def update_payment(payment_id: int) -> Response:
    """支払履歴を更新する(部分更新対応)."""
    user_id = get_jwt_identity()
    json_data = request.get_json()
    if not json_data:
        msg = "Request body is empty"
        raise BadRequestError(msg)

    try:
        # Marshmallow validation
        update_data = PaymentUpdateRequestSchema().load(json_data)

        # Service call
        updated_payment = payment_history_service.update_payment(
            user_id=user_id, payment_id=payment_id, updates=update_data,
        )

        return jsonify({"data": updated_payment.to_dict()})

    except ResourceNotFoundError as e:
        return jsonify({"error": {"code": 404, "message": str(e)}}), 404
    except ForbiddenError:
        # Hide existence for security reasons (Requirement 1.5)
        return (
            jsonify({"error": {"code": 404, "message": "Payment history not found"}}),
            404,
        )
    except MarshmallowValidationError as e:
        return jsonify({"error": {"code": 400, "message": e.messages}}), 400


@payment_history_bp.route("/payments/<int:payment_id>", methods=["DELETE"])
@jwt_required()
def delete_payment(payment_id: int) -> Response:
    """支払履歴を削除する."""
    user_id = get_jwt_identity()

    try:
        payment_history_service.delete_payment(user_id=user_id, payment_id=payment_id)
        return jsonify({}), 204

    except ResourceNotFoundError as e:
        return jsonify({"error": {"code": 404, "message": str(e)}}), 404
    except ForbiddenError:
        # Hide existence for security reasons (Requirement 1.5)
        return (
            jsonify({"error": {"code": 404, "message": "Payment history not found"}}),
            404,
        )
