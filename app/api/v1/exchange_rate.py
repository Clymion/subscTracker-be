"""
API endpoint for retrieving exchange rates.
"""
from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from flask import Blueprint, abort, current_app, request
from flask_jwt_extended import jwt_required

from app.common.response_utils import success_response
from app.constants import ValidationConstants
from app.exceptions import ResourceNotFoundError
from app.models import db
from app.repositories.exchange_rate_repository import ExchangeRateRepository
from app.services.exchange_rate_service import ExchangeRateService

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

exchange_rate_bp = Blueprint("exchange_rate_bp", __name__)


def is_valid_currency_code(code: str) -> bool:
    """Validate if a string is a 3-letter currency code."""
    return (
        isinstance(code, str)
        and len(code) == ValidationConstants.CURRENCY_CODE_LENGTH
        and code.isalpha()
    )


@exchange_rate_bp.route("/exchange-rates", methods=["GET"])
@jwt_required()
def get_exchange_rates() -> tuple[dict, int]:
    """
    Get exchange rates for a given base currency and optional target currencies and date.
    """
    # 1. Parse and validate query parameters
    date_str = request.args.get("date")
    base_currency = request.args.get("base_currency", "USD")
    target_currencies_str = request.args.get("target_currencies")

    target_date = date.today()  # noqa: DTZ011
    if date_str:
        try:
            target_date = date.fromisoformat(date_str)
        except ValueError:
            abort(400, description="Invalid date format. Use YYYY-MM-DD.")

    if not is_valid_currency_code(base_currency):
        abort(400, description="Invalid currency code provided.")

    target_currencies = []
    if target_currencies_str:
        target_currencies = [c.strip().upper() for c in target_currencies_str.split(",")]
        if not all(is_valid_currency_code(c) for c in target_currencies):
            abort(400, description="Invalid currency code provided.")

    try:
        # 2. Dependency Injection
        session: Session = db.session
        repo = ExchangeRateRepository(session)
        service = ExchangeRateService(repo)

        # 3. Call the service
        rates = service.get_rates_for_base_currency(
            target_date, base_currency, target_currencies,
        )

        # 4. Format the response
        response_data = {
            "date": target_date.isoformat(),
            "base_currency": base_currency,
            "rates": rates,
        }
        return success_response(response_data)

    except ResourceNotFoundError:
        current_app.logger.warning(
            "Exchange rates not found for base %s on %s", base_currency, target_date,
        )
        abort(404, description="Exchange rates not found for the given criteria.")
    except Exception:
        current_app.logger.exception(
            "Unexpected error in get_exchange_rates",
        )
        abort(500, description="An unexpected error occurred")
