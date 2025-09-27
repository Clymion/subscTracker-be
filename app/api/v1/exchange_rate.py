"""
API endpoint for retrieving exchange rates.
"""
from datetime import date

from flask import Blueprint, abort, current_app, request
from sqlalchemy.orm import Session

from app.common.response_utils import success_response
from app.exceptions import ResourceNotFoundError
from app.models import db
from app.repositories.exchange_rate_repository import ExchangeRateRepository
from app.services.exchange_rate_service import ExchangeRateService

exchange_rate_bp = Blueprint("exchange_rate_bp", __name__)


@exchange_rate_bp.route("/exchange-rates", methods=["GET"])
def get_exchange_rate() -> tuple[dict, int]:
    """Get the exchange rate for a given currency pair and date."""
    # Parameter validation
    from_currency = request.args.get("from_currency")
    to_currency = request.args.get("to_currency")
    date_str = request.args.get("date")

    if not from_currency or not to_currency:
        abort(400, description="Missing required query parameters")

    target_date = date.today()
    if date_str:
        try:
            target_date = date.fromisoformat(date_str)
        except ValueError:
            abort(400, description="Invalid date format")

    try:
        # Dependency injection is simplified here for clarity.
        # In a real app, you might use Flask-Injector or a similar library.
        session: Session = db.session
        repo = ExchangeRateRepository(session)
        service = ExchangeRateService(repo)

        # Get rate
        rate = service.get_exchange_rate(target_date, from_currency, to_currency)

        return success_response({"rate": rate.rate, "date": rate.date.isoformat()})

    except ResourceNotFoundError:
        current_app.logger.warning(
            "Exchange rate not found for %s-%s on %s",
            from_currency,
            to_currency,
            target_date,
        )
        abort(404, description="Exchange rate not found")
    except Exception as e:
        current_app.logger.exception(
            "Unexpected error in get_exchange_rate: %s", e,
        )
        abort(500, description="An unexpected error occurred")
