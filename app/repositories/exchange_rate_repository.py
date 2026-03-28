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
        """
        Find the most recent rates for each currency pair based on a single base currency.

        Args:
            target_date: The target date to find rates for.
            base_currency: The base currency (to_currency) to find rates for.
                For example, if base_currency is "JPY", this method returns rates
                where to_currency="JPY" (e.g., USD→JPY, EUR→JPY).
                This is useful for converting foreign subscription prices to the user's base currency.

        Returns:
            List of ExchangeRate objects with to_currency == base_currency.
        """
        # Subquery to find the latest date for each currency pair
        latest_dates_subquery = (
            self.session.query(
                ExchangeRate.from_currency,
                func.max(ExchangeRate.date).label("max_date"),
            )
            .filter(
                ExchangeRate.to_currency == base_currency,
                ExchangeRate.date <= target_date,
            )
            .group_by(ExchangeRate.from_currency)
            .subquery("latest_rates")
        )

        # Join the original table with the subquery to get the full records
        query =  (
            self.session.query(ExchangeRate)
            .join(
                latest_dates_subquery,
                and_(
                    ExchangeRate.to_currency == base_currency,
                    ExchangeRate.from_currency == latest_dates_subquery.c.from_currency,
                    ExchangeRate.date == latest_dates_subquery.c.max_date,
                ),
            )
            
        )

        # デバッグ: 実際に実行されるSQLを出力
        from sqlalchemy.dialects import mysql
        from app.common.logging_setup import get_logger
        logger = get_logger(__name__)
        logger.debug("=== DEBUG SQL ===")
        logger.debug(query.statement.compile(dialect=mysql.dialect(), compile_kwargs={"literal_binds": True}))
        logger.debug(query.all())
        logger.debug("=================")
        return query.all()

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
