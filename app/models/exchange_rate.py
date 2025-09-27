"""
ExchangeRate model for storing daily currency exchange rates.
"""

from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.models import db


class ExchangeRate(db.Model):
    """
    ExchangeRate model representing the conversion rate between two currencies for a specific date.
    """

    __tablename__ = "exchange_rates"

    # Composite primary key
    from_currency: Mapped[str] = mapped_column(String(3), primary_key=True)
    to_currency: Mapped[str] = mapped_column(String(3), primary_key=True)
    date: Mapped[date] = mapped_column(Date, primary_key=True)

    # Rate and source
    rate: Mapped[float] = mapped_column(Float, nullable=False)
    source: Mapped[str] = mapped_column(String(50), nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    def __repr__(self) -> str:
        """String representation of the exchange rate."""
        return (
            f"<ExchangeRate {self.from_currency} to {self.to_currency} on {self.date}:"
            f" {self.rate}>"
        )
