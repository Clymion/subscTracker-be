"""Service layer for handling exchange rate logic."""

from datetime import date

from app.constants import ErrorMessages
from app.exceptions import ResourceNotFoundError
from app.models.exchange_rate import ExchangeRate
from app.repositories.exchange_rate_repository import ExchangeRateRepository


class ExchangeRateService:
    """Service for exchange rate business logic."""

    def __init__(self, exchange_rate_repository: ExchangeRateRepository) -> None:
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

    def get_rates_for_base_currency(
        self,
        target_date: date,
        base_currency: str,
        target_currencies: list[str] | None,
    ) -> dict[str, float]:
        """
        Get a dictionary of exchange rates for a specific date and base currency.

        Args:
            target_date: The target date for the exchange rates.
            base_currency: The currency to convert from.
            target_currencies: An optional list of target currencies to filter by.

        Returns:
            A dictionary mapping target currency codes to their rates.
        """
        rates = self.exchange_rate_repository.find_rates_by_base_currency(
            target_date=target_date,
            base_currency=base_currency,
        )

        if not rates:
            raise ResourceNotFoundError(ErrorMessages.EXCHANGE_RATE_NOT_FOUND)

        rate_dict = {rate.to_currency: rate.rate for rate in rates}

        if target_currencies:
            rate_dict = {
                currency: rate
                for currency, rate in rate_dict.items()
                if currency in target_currencies
            }

        return rate_dict
