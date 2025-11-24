"""
Payment History APIエンドポイント
"""

from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from flask import Blueprint, jsonify, request

from flask_jwt_extended import get_jwt_identity, jwt_required



from app.models import db
from app.models.payment_history import PaymentHistory

from app.services.payment_history_service import PaymentHistoryService



payment_history_bp = Blueprint("payment_history_bp", __name__)



payment_history_service = PaymentHistoryService(session=db.session)





@payment_history_bp.route("/payments", methods=["GET"])

@jwt_required()

def get_payment_histories():

    """支払履歴一覧を取得する"""

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
        if sort_by not in PaymentHistory.__table__.columns.keys():
            raise ValueError(f"Invalid sort_by column: {sort_by}")

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

        return jsonify(response_data), 200

    except ValueError as e:

        return jsonify({"error": {"code": 400, "message": str(e)}}), 400


