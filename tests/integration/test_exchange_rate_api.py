"""
Integration tests for the Exchange Rate API endpoint.
"""
from collections.abc import Generator
from datetime import date

import pytest
from flask.testing import FlaskClient
from sqlalchemy.orm import Session

from app.models.exchange_rate import ExchangeRate
from tests.helpers import (
    assert_error_response,
    assert_success_response,
    make_auth_headers,
)


@pytest.fixture
def setup_exchange_rates(clean_db: Generator[Session, None, None]) -> Session:
    """Fixture to set up exchange rates for testing."""
    rates = [
        ExchangeRate(
            from_currency="USD",
            to_currency="JPY",
            date=date(2025, 9, 26),
            rate=145.0,
            source="test",
        ),
        ExchangeRate(
            from_currency="USD",
            to_currency="JPY",
            date=date(2025, 9, 25),
            rate=144.5,
            source="test",
        ),
        ExchangeRate(
            from_currency="EUR",
            to_currency="USD",
            date=date(2025, 9, 26),
            rate=1.08,
            source="test",
        ),
    ]
    clean_db.add_all(rates)
    clean_db.commit()
    return clean_db


@pytest.mark.api
class TestGetMultipleExchangeRatesAPI:
    """Test cases for GET /api/v1/exchange-rates (Refactored)"""

    def test_get_rates_with_base_currency_returns_200(
        self, client: FlaskClient, setup_exchange_rates: Session,
    ):
        """[Success] GET /exchange-rates: Returns 200 with rates for a specific base currency."""
        headers = make_auth_headers()
        response = client.get(
            "/api/v1/exchange-rates?base_currency=JPY", headers=headers,
        )
        data = assert_success_response(response, 200)
        assert data["data"]["base_currency"] == "JPY"
        assert "USD" in data["data"]["rates"]
        assert "EUR" not in data["data"]["rates"]

    def test_get_rates_with_target_currencies_returns_200(
        self, client: FlaskClient, setup_exchange_rates: Session,
    ):
        """[Success] GET /exchange-rates: Returns 200 with filtered rates for target_currencies."""
        headers = make_auth_headers()
        # Add EUR rate for USD to test filtering
        setup_exchange_rates.add(
            ExchangeRate(
                from_currency="EUR",
                to_currency="JPY",
                date=date(2025, 9, 26),
                rate=0.92,
                source="test",
            )
        )
        setup_exchange_rates.commit()

        response = client.get(
            "/api/v1/exchange-rates?base_currency=JPY&target_currencies=JPY,EUR",
            headers=headers,
        )
        data = assert_success_response(response, 200)
        assert "JPY" in data["data"]["rates"]
        assert "EUR" in data["data"]["rates"]

    def test_get_rates_with_specific_date_returns_200(
        self, client: FlaskClient, setup_exchange_rates: Session,
    ):
        """[Success] GET /exchange-rates: Returns 200 with rates for a specific date."""
        headers = make_auth_headers()
        response = client.get(
            "/api/v1/exchange-rates?base_currency=JPY&date=2025-09-25",
            headers=headers,
        )
        data = assert_success_response(response, 200)
        assert data["data"]["date"] == "2025-09-25"
        assert data["data"]["rates"]["USD"] == 144.5

    def test_get_rates_no_params_returns_defaults_200(
        self, client: FlaskClient, setup_exchange_rates: Session,
    ):
        """[Success] GET /exchange-rates: Returns 200 with default params (base=USD, latest date)."""
        headers = make_auth_headers()
        response = client.get("/api/v1/exchange-rates", headers=headers)
        data = assert_success_response(response, 200)
        assert data["data"]["base_currency"] == "USD"
        assert data["data"]["date"] == str(date.today())

    def test_get_rates_invalid_date_format_returns_400(
        self, client: FlaskClient, setup_exchange_rates: Session,
    ):
        """[Failure] GET /exchange-rates: Returns 400 for invalid date format."""
        headers = make_auth_headers()
        response = client.get(
            "/api/v1/exchange-rates?date=invalid-date", headers=headers,
        )
        assert_error_response(response, 400, "Invalid date format. Use YYYY-MM-DD.")

    def test_get_rates_invalid_currency_code_returns_400(
        self, client: FlaskClient, setup_exchange_rates: Session,
    ):
        """[Failure] GET /exchange-rates: Returns 400 for invalid currency code."""
        headers = make_auth_headers()
        response = client.get(
            "/api/v1/exchange-rates?base_currency=INVALID", headers=headers,
        )
        assert_error_response(response, 400, "Invalid currency code provided.")

    def test_get_rates_not_found_returns_404(
        self, client: FlaskClient, setup_exchange_rates: Session,
    ):
        """[Failure] GET /exchange-rates: Returns 404 if no rates are found."""
        headers = make_auth_headers()
        response = client.get(
            "/api/v1/exchange-rates?base_currency=GBP", headers=headers,
        )
        assert_error_response(
            response, 404, "Exchange rates not found for the given criteria.",
        )

    def test_get_rates_with_all_params_returns_200(
        self, client: FlaskClient, setup_exchange_rates: Session,
    ):
        """
        [Success] GET /exchange-rates: Returns 200 with combined date, base, and target filters.
        """
        headers = make_auth_headers()
        # Add more data for a comprehensive test
        setup_exchange_rates.add_all(
            [
                ExchangeRate(
                    from_currency="EUR",
                    to_currency="USD",
                    date=date(2025, 9, 25),
                    rate=1.13,
                    source="test",
                ),
                ExchangeRate(
                    from_currency="JPY",
                    to_currency="USD",
                    date=date(2025, 9, 25),
                    rate=144.5,
                    source="test",
                ),
            ],
        )
        setup_exchange_rates.commit()

        response = client.get(
            "/api/v1/exchange-rates?date=2025-09-25&base_currency=USD&target_currencies=JPY,EUR",
            headers=headers,
        )
        data = assert_success_response(response, 200)
        assert data["data"]["date"] == "2025-09-25"
        assert data["data"]["base_currency"] == "USD"
        assert "JPY" in data["data"]["rates"]
        assert "EUR" in data["data"]["rates"]
        assert "GBP" not in data["data"]["rates"]
        assert data["data"]["rates"]["JPY"] == 144.5
        assert data["data"]["rates"]["EUR"] == 1.13

    def test_get_rates_no_auth_token_returns_401(self, client: FlaskClient):
        """[Failure] GET /exchange-rates: Returns 401 if auth token is missing."""
        response = client.get("/api/v1/exchange-rates")
        assert_error_response(response, 401, "Missing Authorization Header")

    def test_get_rates_invalid_target_currency_returns_400(self, client: FlaskClient):
        """[Failure] GET /exchange-rates: Returns 400 for invalid target currency code."""
        headers = make_auth_headers()
        response = client.get(
            "/api/v1/exchange-rates?target_currencies=INVALID", headers=headers
        )
        assert_error_response(response, 400, "Invalid currency code provided.")
