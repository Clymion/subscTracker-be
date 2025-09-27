"""
Integration tests for the Exchange Rate API endpoint.
"""
from collections.abc import Generator
from datetime import date

import pytest
from flask.testing import FlaskClient
from sqlalchemy.orm import Session

from app.models.exchange_rate import ExchangeRate
from tests.helpers import assert_error_response, assert_success_response


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
class TestGetExchangeRateAPI:
    """Test cases for GET /api/v1/exchange-rates"""

    def test_get_rate_with_exact_date_returns_200(
        self,
        client: FlaskClient,
        setup_exchange_rates: Session,
    ):
        """[Success] GET /exchange-rates: Returns 200 with the correct rate for an exact date match."""
        # Act
        response = client.get(
            "/api/v1/exchange-rates?date=2025-09-26&from_currency=USD&to_currency=JPY",
        )

        # Assert
        data = assert_success_response(response, 200)
        assert data["data"]["rate"] == 145.0

    def test_get_rate_with_fallback_date_returns_200(
        self,
        client: FlaskClient,
        setup_exchange_rates: Session,
    ):
        """[Success] GET /exchange-rates: Returns 200 with the most recent rate on fallback."""
        # Act
        response = client.get(
            "/api/v1/exchange-rates?date=2025-09-27&from_currency=USD&to_currency=JPY",
        )

        # Assert
        data = assert_success_response(response, 200)
        assert data["data"]["rate"] == 145.0  # Falls back to 2025-09-26

    def test_get_rate_without_date_returns_most_recent_200(
        self,
        client: FlaskClient,
        setup_exchange_rates: Session,
    ):
        """[Success] GET /exchange-rates: Returns 200 with the most recent rate if date is omitted."""
        # Act
        response = client.get("/api/v1/exchange-rates?from_currency=USD&to_currency=JPY")

        # Assert
        data = assert_success_response(response, 200)
        assert data["data"]["rate"] == 145.0  # Most recent is 2025-09-26

    def test_get_rate_not_found_returns_404(
        self,
        client: FlaskClient,
        setup_exchange_rates: Session,
    ):
        """[Failure] GET /exchange-rates: Returns 404 if no rate is found."""
        # Act
        response = client.get(
            "/api/v1/exchange-rates?date=2025-09-24&from_currency=USD&to_currency=JPY",
        )

        # Assert
        assert_error_response(response, 404, "Exchange rate not found")

    def test_get_rate_missing_param_returns_400(
        self, client: FlaskClient, setup_exchange_rates: Session,
    ):
        """[Failure] GET /exchange-rates: Returns 400 if a currency parameter is missing."""
        # Act
        response = client.get("/api/v1/exchange-rates?date=2025-09-26&from_currency=USD")

        # Assert
        assert_error_response(response, 400, "Missing required query parameters")

    def test_get_rate_invalid_date_format_returns_400(
        self, client: FlaskClient, setup_exchange_rates: Session,
    ):
        """[Failure] GET /exchange-rates: Returns 400 for an invalid date format."""
        # Act
        response = client.get(
            "/api/v1/exchange-rates?date=26-09-2025&from_currency=USD&to_currency=JPY",
        )

        # Assert
        assert_error_response(response, 400, "Invalid date format")
