"""Repository for exchange rate data access logic."""

from datetime import date
from typing import Optional

from sqlalchemy.orm import Session

from app.models.exchange_rate import ExchangeRate


class ExchangeRateRepository:
    """Repository for exchange rate data access logic."""

    def __init__(self, session: Session) -> None:
        """
        Initialize the repository with a database session.

        Args:
            session: The SQLAlchemy Session object.
        """
        self.session = session

    def find_rate_by_date(
        self,
        target_date: date,
        from_currency: str,
        to_currency: str,
    ) -> Optional[ExchangeRate]:
        """Find the most recent exchange rate for a given currency pair on or before a specific date."""
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
