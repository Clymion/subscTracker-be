"""Service layer for handling exchange rate logic."""

from datetime import date

from app.constants import ErrorMessages
from app.exceptions import ExchangeRateNotFoundError, ResourceNotFoundError
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
    ) -> tuple[ExchangeRate, bool]:
        """
        Get the exchange rate for a specific date and currency pair.

        If a direct rate is not found, it attempts to find the inverse rate.

        Args:
            target_date: The target date for the exchange rate.
            from_currency: The currency to convert from.
            to_currency: The currency to convert to.

        Returns:
            A tuple containing the actual ExchangeRate object from the database
            and a boolean indicating if the rate was inverted.

        Raises:
            ExchangeRateNotFoundError: If no exchange rate is found for either direction.
        """
        # Try to find the direct rate
        direct_rate = self.exchange_rate_repository.find_rate_by_date(
            target_date=target_date,
            from_currency=from_currency,
            to_currency=to_currency,
        )
        if direct_rate:
            return direct_rate, False

        # If direct rate is not found, try to find the inverse rate
        inverse_rate = self.exchange_rate_repository.find_rate_by_date(
            target_date=target_date,
            from_currency=to_currency,
            to_currency=from_currency,
        )
        if inverse_rate:
            return inverse_rate, True

        # If neither is found, raise an error
        raise ExchangeRateNotFoundError(target_date, from_currency, to_currency)

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

        rate_dict = {rate.from_currency: rate.rate for rate in rates}

        if target_currencies:
            rate_dict = {
                currency: rate
                for currency, rate in rate_dict.items()
                if currency in target_currencies
            }

        # If no rates are found and the base currency itself is not a target,
        # then we should raise a not found error.
        if not rate_dict and (not target_currencies or base_currency not in target_currencies):
            # Create a pseudo to_currency for the error message since we don't
            # have a specific one (multiple target currencies were requested)
            to_currency = ",".join(target_currencies) if target_currencies else "any"
            raise ExchangeRateNotFoundError(target_date, base_currency, to_currency)

        # Add the base currency with a rate of 1.0 if it was requested, or if no
        # specific currencies were requested.
        if not target_currencies or base_currency in target_currencies:
            rate_dict[base_currency] = 1.0

        return rate_dict
