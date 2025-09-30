"""Repository for exchange rate data access logic."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import and_, func

from app.models.exchange_rate import ExchangeRate

if TYPE_CHECKING:
    from datetime import date

    from sqlalchemy.orm import Session


class ExchangeRateRepository:
    """Repository for exchange rate data access logic."""

    def __init__(self, session: Session) -> None:
        """
        Initialize the repository with a database session.

        Args:
            session: The SQLAlchemy Session object.
        """
        self.session = session

    def find_rates_by_base_currency(
        self,
        target_date: date,
        base_currency: str,
    ) -> list[ExchangeRate]:
        """Find the most recent rates for each currency pair based on a single base currency."""
        # Subquery to find the latest date for each currency pair
        latest_dates_subquery = (
            self.session.query(
                ExchangeRate.to_currency,
                func.max(ExchangeRate.date).label("max_date"),
            )
            .filter(
                ExchangeRate.from_currency == base_currency,
                ExchangeRate.date <= target_date,
            )
            .group_by(ExchangeRate.to_currency)
            .subquery("latest_rates")
        )

        # Join the original table with the subquery to get the full records
        return (
            self.session.query(ExchangeRate)
            .join(
                latest_dates_subquery,
                and_(
                    ExchangeRate.from_currency == base_currency,
                    ExchangeRate.to_currency == latest_dates_subquery.c.to_currency,
                    ExchangeRate.date == latest_dates_subquery.c.max_date,
                ),
            )
            .all()
        )

    def find_rate_by_date(
        self,
        target_date: date,
        from_currency: str,
        to_currency: str,
    ) -> ExchangeRate | None:
        """Find the most recent rate for a currency pair on or before a specific date."""
        return (
            self.session.query(ExchangeRate)
            .filter(
                ExchangeRate.from_currency == from_currency,
                ExchangeRate.to_currency == to_currency,
                ExchangeRate.date <= target_date,
            )
            .order_by(ExchangeRate.date.desc())
            .first()
        )
