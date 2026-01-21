import logging
from datetime import date, datetime
from typing import Any

from sqlalchemy import (
    REAL,
    Date,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.models import db

logger = logging.getLogger(__name__)


class PaymentHistory(db.Model):
    __tablename__ = "payment_histories"

    payment_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    subscription_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("subscriptions.subscription_id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    subscription_name: Mapped[str] = mapped_column(String(100), nullable=False)
    payment_date: Mapped[date] = mapped_column(Date, nullable=False)
    amount: Mapped[float] = mapped_column(REAL, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    rate_from_currency: Mapped[str] = mapped_column(String(3), nullable=False)
    rate_to_currency: Mapped[str] = mapped_column(String(3), nullable=False)
    rate_date: Mapped[date] = mapped_column(Date, nullable=False)
    exchange_rate: Mapped[float | None] = mapped_column(REAL, nullable=True)
    converted_amount: Mapped[float | None] = mapped_column(REAL, nullable=True)
    payment_method: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    def __init__(self, **kwargs: Any):
        logger.info("PaymentHistory created with args: %s", kwargs)
        super().__init__(**kwargs)

    user = relationship("User", back_populates="payment_histories")
    subscription = relationship("Subscription", back_populates="payment_histories")

    def to_dict(self) -> dict[str, Any]:
        """支払履歴モデルを辞書に変換する"""
        return {
            "payment_id": self.payment_id,
            "user_id": self.user_id,
            "subscription_id": self.subscription_id,
            "subscription_name": self.subscription_name,
            "payment_date": self.payment_date.isoformat(),
            "amount": self.amount,
            "currency": self.currency,
            "rate_from_currency": self.rate_from_currency,
            "rate_to_currency": self.rate_to_currency,
            "rate_date": self.rate_date.isoformat() if self.rate_date else None,
            "exchange_rate": self.exchange_rate,
            "converted_amount": self.converted_amount,
            "payment_method": self.payment_method,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    __table_args__ = (
        ForeignKeyConstraint(
            ["rate_from_currency", "rate_to_currency", "rate_date"],
            [
                "exchange_rates.from_currency",
                "exchange_rates.to_currency",
                "exchange_rates.date",
            ],
        ),
    )
