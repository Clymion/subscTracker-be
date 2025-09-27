"""Service layer for handling exchange rate logic."""

from datetime import date

from app.constants import ErrorMessages
from app.exceptions import ResourceNotFoundError
from app.models.exchange_rate import ExchangeRate
from app.repositories.exchange_rate_repository import ExchangeRateRepository


class ExchangeRateService:
    """Service for exchange rate business logic."""

    def __init__(self, exchange_rate_repository: ExchangeRateRepository):
        """
        Initialize the service with a repository.

        Args:
            exchange_rate_repository: The repository for exchange rate data.
        """
        self.exchange_rate_repository = exchange_rate_repository

    def get_exchange_rate(
        self,
        target_date: date,
        from_currency: str,
        to_currency: str,
    ) -> ExchangeRate:
        """
        Get the exchange rate for a specific date and currency pair.

        Args:
            target_date: The target date for the exchange rate.
            from_currency: The currency to convert from.
            to_currency: The currency to convert to.

        Returns:
            The ExchangeRate object.

        Raises:
            ResourceNotFoundError: If no exchange rate is found.
        """
        rate = self.exchange_rate_repository.find_rate_by_date(
            target_date=target_date,
            from_currency=from_currency,
            to_currency=to_currency,
        )
        if rate is None:
            raise ResourceNotFoundError(ErrorMessages.EXCHANGE_RATE_NOT_FOUND)
        return rate
