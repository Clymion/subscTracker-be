"""
Unit tests for the ExchangeRateService.
"""
from datetime import date
from unittest.mock import MagicMock

import pytest

from app.exceptions import ResourceNotFoundError
from app.models.exchange_rate import ExchangeRate
from app.services.exchange_rate_service import ExchangeRateService


@pytest.fixture
def mock_exchange_rate_repo() -> MagicMock:
    """Fixture to create a mock ExchangeRateRepository."""
    return MagicMock()


@pytest.fixture
def exchange_rate_service(
    mock_exchange_rate_repo: MagicMock,
) -> ExchangeRateService:
    """Fixture to create an ExchangeRateService with a mock repository."""
    return ExchangeRateService(exchange_rate_repository=mock_exchange_rate_repo)


@pytest.mark.unit
class TestExchangeRateServiceGet:
    """Test cases for the get_exchange_rate method."""

    def test_get_exchange_rate_found(
        self,
        exchange_rate_service: ExchangeRateService,
        mock_exchange_rate_repo: MagicMock,
    ):
        """Test that the service returns an exchange rate when the repository finds one."""
        # Arrange
        target_date = date(2025, 9, 27)
        from_currency = "USD"
        to_currency = "JPY"
        expected_rate = ExchangeRate(
            from_currency=from_currency,
            to_currency=to_currency,
            date=target_date,
            rate=145.5,
            source="test",
        )
        mock_exchange_rate_repo.find_rate_by_date.return_value = expected_rate

        # Act
        result, is_inverted = exchange_rate_service.get_exchange_rate(
            target_date=target_date,
            from_currency=from_currency,
            to_currency=to_currency,
        )

        # Assert
        assert result is not None
        assert result.rate == 145.5
        assert is_inverted is False
        mock_exchange_rate_repo.find_rate_by_date.assert_called_once_with(
            target_date=target_date,
            from_currency=from_currency,
            to_currency=to_currency,
        )

    def test_get_exchange_rate_not_found_raises_error(
        self,
        exchange_rate_service: ExchangeRateService,
        mock_exchange_rate_repo: MagicMock,
    ):
        """Test that ResourceNotFoundError is raised when the repository returns None."""
        # Arrange
        target_date = date(2025, 9, 27)
        from_currency = "USD"
        to_currency = "JPY"
        mock_exchange_rate_repo.find_rate_by_date.return_value = None

        # Act & Assert
        with pytest.raises(ResourceNotFoundError):
            exchange_rate_service.get_exchange_rate(
                target_date=target_date,
                from_currency=from_currency,
                to_currency=to_currency,
            )
        
        assert mock_exchange_rate_repo.find_rate_by_date.call_count == 2
        mock_exchange_rate_repo.find_rate_by_date.assert_any_call(
            target_date=target_date,
            from_currency=from_currency,
            to_currency=to_currency,
        )
        mock_exchange_rate_repo.find_rate_by_date.assert_any_call(
            target_date=target_date,
            from_currency=to_currency,
            to_currency=from_currency,
        )

@pytest.mark.unit
class TestGetRatesForBaseCurrency:
    """Test cases for the get_rates_for_base_currency method."""

    def test_get_rates_for_base_currency_found(
        self,
        exchange_rate_service: ExchangeRateService,
        mock_exchange_rate_repo: MagicMock,
    ):
        """Test that the service returns a dictionary of rates when the repository finds them."""
        # Arrange
        target_date = date(2025, 9, 27)
        base_currency = "USD"
        repo_results = [
            ExchangeRate(from_currency="USD", to_currency="JPY", date=date(2025, 9, 26), rate=145.0),
            ExchangeRate(from_currency="USD", to_currency="EUR", date=date(2025, 9, 27), rate=0.95),
        ]
        mock_exchange_rate_repo.find_rates_by_base_currency.return_value = repo_results

        # Act
        result = exchange_rate_service.get_rates_for_base_currency(
            target_date=target_date,
            base_currency=base_currency,
            target_currencies=None,
        )

        # Assert
        assert result == {"JPY": 145.0, "EUR": 0.95, "USD": 1.0}
        mock_exchange_rate_repo.find_rates_by_base_currency.assert_called_once_with(
            target_date=target_date,
            base_currency=base_currency,
        )

    def test_get_rates_for_base_currency_with_targets(
        self,
        exchange_rate_service: ExchangeRateService,
        mock_exchange_rate_repo: MagicMock,
    ):
        """Test that the service correctly filters rates by target_currencies."""
        # Arrange
        target_date = date(2025, 9, 27)
        base_currency = "USD"
        target_currencies = ["JPY"]
        repo_results = [
            ExchangeRate(from_currency="USD", to_currency="JPY", date=date(2025, 9, 26), rate=145.0),
            ExchangeRate(from_currency="USD", to_currency="EUR", date=date(2025, 9, 27), rate=0.95),
        ]
        mock_exchange_rate_repo.find_rates_by_base_currency.return_value = repo_results

        # Act
        result = exchange_rate_service.get_rates_for_base_currency(
            target_date=target_date,
            base_currency=base_currency,
            target_currencies=target_currencies,
        )

        # Assert
        assert result == {"JPY": 145.0}
        mock_exchange_rate_repo.find_rates_by_base_currency.assert_called_once_with(
            target_date=target_date,
            base_currency=base_currency,
        )

    def test_get_rates_for_base_currency_not_found(
        self,
        exchange_rate_service: ExchangeRateService,
        mock_exchange_rate_repo: MagicMock,
    ):
        """Test that ResourceNotFoundError is raised when no rates are found."""
        # Arrange
        target_date = date(2025, 9, 27)
        base_currency = "USD"
        mock_exchange_rate_repo.find_rates_by_base_currency.return_value = []

        # Act & Assert
        with pytest.raises(ResourceNotFoundError):
            exchange_rate_service.get_rates_for_base_currency(
                target_date=target_date,
                base_currency=base_currency,
                target_currencies=None,
            )