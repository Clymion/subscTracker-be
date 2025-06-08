"""
Subscription model for managing user subscriptions.

This module defines the Subscription SQLAlchemy model with all required fields,
relationships, and business logic methods for subscription management.
"""

from datetime import date, datetime
from typing import Optional

from sqlalchemy import REAL, Date, DateTime, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.constants import (
    CurrencyConstants,
    ErrorMessages,
    PaymentFrequency,
    SubscriptionStatus,
)
from app.models import db
from app.models.label import Label  # Labelをインポート


class Subscription(db.Model):
    """
    Subscription model representing a user's subscription to a service.

    This model handles subscription data including pricing, payment schedules,
    status management, and relationships with users and labels.
    """

    __tablename__ = "subscriptions"

    # Primary key
    subscription_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    # Foreign key to users table
    user_id: Mapped[int] = mapped_column(
        Integer,
        db.ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Basic subscription information
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    price: Mapped[float] = mapped_column(REAL, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, index=True)

    # Payment schedule
    initial_payment_date: Mapped[date] = mapped_column(Date, nullable=False)
    next_payment_date: Mapped[date] = mapped_column(Date, nullable=False)
    payment_frequency: Mapped[str] = mapped_column(String(20), nullable=False)
    payment_method: Mapped[str] = mapped_column(String(50), nullable=False)

    # Status and optional fields
    status: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

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

    # Composite indexes for optimized queries
    __table_args__ = (
        # User + Status composite index for filtering
        Index("idx_subscriptions_user_status", "user_id", "status"),
        # Pagination indexes for different sorting options
        Index("idx_subscriptions_pagination", "user_id", "created_at"),
        Index("idx_subscriptions_pagination_name", "user_id", "name"),
        Index("idx_subscriptions_pagination_price", "user_id", "price"),
    )

    # Relationships
    user = relationship("User", back_populates="subscriptions")
    labels: Mapped[list["Label"]] = relationship(
        "Label",
        secondary="subscription_labels",
        back_populates="subscriptions",
        lazy="select",
    )

    def __repr__(self) -> str:
        """String representation of the subscription."""
        return f"<Subscription {self.name} - {self.currency}{self.price}>"

    def __str__(self) -> str:
        """Human-readable string representation."""
        return f"{self.name} ({self.status})"

    def to_dict(self) -> dict:
        """サブスクリプションオブジェクトを辞書に変換するのだ。"""
        return {
            "subscription_id": self.subscription_id,
            "user_id": self.user_id,
            "name": self.name,
            "price": self.price,
            "currency": self.currency,
            "initial_payment_date": self.initial_payment_date.isoformat(),
            "next_payment_date": self.next_payment_date.isoformat(),
            "payment_frequency": self.payment_frequency,
            "payment_method": self.payment_method,
            "status": self.status,
            "url": self.url,
            "notes": self.notes,
            "image_url": self.image_url,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "labels": [label.to_dict() for label in self.labels],
        }

    # Validation methods
    def validate_currency(self) -> None:
        """Validate that currency is supported."""
        # Normalize currency to uppercase first
        if self.currency:
            self.currency = self.currency.upper()

        if not CurrencyConstants.is_valid(self.currency):
            msg = f"{ErrorMessages.UNSUPPORTED_CURRENCY}: {self.currency}"
            raise ValueError(msg)

    def validate_status(self) -> None:
        """Validate that status is valid."""
        if not SubscriptionStatus.is_valid(self.status):
            msg = f"{ErrorMessages.INVALID_STATUS}: {self.status}"
            raise ValueError(msg)

    def validate_payment_frequency(self) -> None:
        """Validate that payment frequency is valid."""
        if not PaymentFrequency.is_valid(self.payment_frequency):
            msg = f"{ErrorMessages.INVALID_PAYMENT_FREQUENCY}: {self.payment_frequency}"
            raise ValueError(msg)

    def validate_price(self) -> None:
        """Validate that price is positive."""
        if self.price <= 0:
            raise ValueError(ErrorMessages.PRICE_MUST_BE_POSITIVE)

    def validate_dates(self) -> None:
        """Validate date relationships."""
        if self.next_payment_date < self.initial_payment_date:
            raise ValueError(ErrorMessages.NEXT_PAYMENT_DATE_BEFORE_INITIAL)

    # Business logic methods
    def is_active(self) -> bool:
        """Check if subscription is currently active."""
        return self.status == SubscriptionStatus.ACTIVE

    def monthly_cost(self) -> float:
        """Calculate monthly cost based on payment frequency."""
        if self.payment_frequency == PaymentFrequency.MONTHLY:
            return self.price
        elif self.payment_frequency == PaymentFrequency.QUARTERLY:
            return self.price / 3
        elif self.payment_frequency == PaymentFrequency.YEARLY:
            return self.price / 12
        else:
            msg = f"{ErrorMessages.UNKNOWN_PAYMENT_FREQUENCY}: {self.payment_frequency}"
            raise ValueError(msg)

    def yearly_cost(self) -> float:
        """Calculate yearly cost based on payment frequency."""
        if self.payment_frequency == PaymentFrequency.MONTHLY:
            return self.price * 12
        elif self.payment_frequency == PaymentFrequency.QUARTERLY:
            return self.price * 4
        elif self.payment_frequency == PaymentFrequency.YEARLY:
            return self.price
        else:
            msg = f"{ErrorMessages.UNKNOWN_PAYMENT_FREQUENCY}: {self.payment_frequency}"
            raise ValueError(msg)

    def calculate_next_payment_date(self, from_date: Optional[date] = None) -> date:
        """
        Calculate next payment date with smart month-end handling.

        Args:
            from_date: Date to calculate from. Defaults to current next_payment_date.

        Returns:
            Next payment date with smart month-end handling.
        """
        if from_date is None:
            from_date = self.next_payment_date

        if self.payment_frequency == PaymentFrequency.MONTHLY:
            return self._add_months(from_date, 1)
        elif self.payment_frequency == PaymentFrequency.QUARTERLY:
            return self._add_months(from_date, 3)
        elif self.payment_frequency == PaymentFrequency.YEARLY:
            return self._add_months(from_date, 12)
        else:
            msg = f"{ErrorMessages.UNKNOWN_PAYMENT_FREQUENCY}: {self.payment_frequency}"
            raise ValueError(msg)

    def _add_months(self, start_date: date, months: int) -> date:
        """
        Add months to a date with smart month-end handling.

        Handles edge cases like:
        - Jan 31 + 1 month = Feb 28/29 (depending on leap year)
        - May 31 + 1 month = Jun 30
        - End-of-month contracts stay end-of-month
        """
        import calendar

        year = start_date.year
        month = start_date.month + months
        day = start_date.day

        # Handle year overflow
        while month > 12:
            year += 1
            month -= 12

        # Smart month-end handling
        # If original date was the last day of the month, make result last day too
        if self._is_last_day_of_month(start_date):
            last_day = calendar.monthrange(year, month)[1]
            return date(year, month, last_day)

        # Handle day overflow (e.g., Jan 31 -> Feb 28/29)
        last_day = calendar.monthrange(year, month)[1]
        day = min(day, last_day)

        return date(year, month, day)

    def _is_last_day_of_month(self, check_date: date) -> bool:
        """Check if date is the last day of its month."""
        import calendar

        last_day = calendar.monthrange(check_date.year, check_date.month)[1]
        return check_date.day == last_day
