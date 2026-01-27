"""Service for handling payment history business logic."""

from datetime import date
from typing import Any

from sqlalchemy.orm import Session

from app.common.logging_setup import get_logger
from app.exceptions import ForbiddenError, ResourceNotFoundError, ValidationError
from app.models.payment_history import PaymentHistory
from app.repositories.payment_history_repository import PaymentHistoryRepository
from app.repositories.subscription_repository import SubscriptionRepository
from app.repositories.user_repository import UserRepository
from app.services.exchange_rate_service import ExchangeRateService

logger = get_logger(__name__)


class PaymentHistoryService:
    """Service for payment history business logic."""

    def __init__(
        self,
        session: Session,
        payment_history_repository: PaymentHistoryRepository,
        user_repository: UserRepository,
        subscription_repository: SubscriptionRepository,
        exchange_rate_service: ExchangeRateService,
    ) -> None:
        """Initialize the service."""
        self.session = session
        self.payment_history_repository = payment_history_repository
        self.user_repository = user_repository
        self.subscription_repository = subscription_repository
        self.exchange_rate_service = exchange_rate_service

    def get_payment_history(
        self,
        user_id: int,
        filters: dict[str, Any],
        sort_by: str,
        sort_order: str,
        limit: int,
        offset: int,
    ) -> tuple[list[Any], int]:
        """Get a list of payment histories for a user."""
        payments = self.payment_history_repository.find_all_by_user_id(
            user_id,
            filters,
            sort_by,
            sort_order,
            limit,
            offset,
        )
        total = self.payment_history_repository.count_all_by_user_id(user_id, filters)
        return payments, total

    def _calculate_exchange_rate_data(
        self, amount: float, currency: str, payment_date: date, base_currency: str,
    ) -> dict[str, Any]:
        """Calculate exchange rate and converted amount."""
        if currency == base_currency:
            return {
                "exchange_rate": 1.0,
                "rate_from_currency": currency,
                "rate_to_currency": currency,
                "rate_date": payment_date,
                "converted_amount": amount,
            }

        try:
            rate_obj, was_inverted = self.exchange_rate_service.get_exchange_rate(
                payment_date,
                from_currency=currency,
                to_currency=base_currency,
            )
        except ResourceNotFoundError as err:
            msg = f"Exchange rate not found for {currency} to {base_currency} on {payment_date}"
            raise ValidationError(msg) from err

        exchange_rate = 1 / rate_obj.rate if was_inverted else rate_obj.rate
        converted_amount = (
            amount * exchange_rate if was_inverted else amount / exchange_rate
        )

        return {
            "exchange_rate": exchange_rate,
            "rate_from_currency": rate_obj.from_currency,
            "rate_to_currency": rate_obj.to_currency,
            "rate_date": rate_obj.date,
            "converted_amount": converted_amount,
        }

    def create_payment(
        self, user_id: int, payment_data: dict[str, Any],
    ) -> PaymentHistory:
        """新しい支払い履歴を作成し、DBに保存する."""
        user = self.user_repository.find_by_id(user_id)
        if not user:
            msg = "User not found"
            raise ResourceNotFoundError(msg)

        subscription = self.subscription_repository.find_by_id(
            payment_data["subscription_id"],
        )
        if not subscription:
            msg = "Subscription not found"
            raise ResourceNotFoundError(msg)

        if subscription.user_id != int(user_id):
            msg = "This subscription does not belong to the current user"
            raise ForbiddenError(msg)

        rate_data = self._calculate_exchange_rate_data(
            amount=payment_data["amount"],
            currency=payment_data["currency"],
            payment_date=payment_data["payment_date"],
            base_currency=user.base_currency,
        )

        payment = PaymentHistory(
            user_id=user_id,
            subscription_id=payment_data["subscription_id"],
            subscription_name=subscription.name,
            payment_date=payment_data["payment_date"],
            amount=payment_data["amount"],
            currency=payment_data["currency"],
            rate_from_currency=rate_data["rate_from_currency"],
            rate_to_currency=rate_data["rate_to_currency"],
            rate_date=rate_data["rate_date"],
            exchange_rate=rate_data["exchange_rate"],
            converted_amount=rate_data["converted_amount"],
            payment_method=payment_data["payment_method"],
        )
        return self.payment_history_repository.save(payment)

    def _update_subscription_if_needed(
        self, payment: PaymentHistory, updates: dict[str, Any], user_id: int,
    ) -> None:
        """Update subscription ID and name if changed."""
        if "subscription_id" not in updates:
            return

        new_sub_id = updates["subscription_id"]
        if new_sub_id == payment.subscription_id:
            return

        subscription = self.subscription_repository.find_by_id(new_sub_id)
        if not subscription:
            msg = "Subscription not found"
            raise ResourceNotFoundError(msg)
        if subscription.user_id != int(user_id):
            msg = "This subscription does not belong to the current user"
            raise ForbiddenError(msg)

        payment.subscription_id = new_sub_id
        payment.subscription_name = subscription.name

    def update_payment(
        self, user_id: int, payment_id: int, updates: dict[str, Any],
    ) -> PaymentHistory:
        """既存の支払い履歴を更新する."""
        payment = self.payment_history_repository.find_by_id(payment_id)
        if not payment:
            msg = "Payment history not found"
            raise ResourceNotFoundError(msg)

        if payment.user_id != int(user_id):
            msg = "This payment history does not belong to the current user"
            raise ForbiddenError(msg)

        if "amount" in updates and updates["amount"] < 0:
            msg = "Amount cannot be negative"
            raise ValidationError(msg)

        self._update_subscription_if_needed(payment, updates, user_id)

        new_currency = updates.get("currency", payment.currency)
        new_date = updates.get("payment_date", payment.payment_date)
        new_amount = updates.get("amount", payment.amount)

        if "currency" in updates or "payment_date" in updates:
            user = self.user_repository.find_by_id(user_id)
            if not user:
                msg = "User not found"
                raise ResourceNotFoundError(msg)

            rate_data = self._calculate_exchange_rate_data(
                amount=new_amount,
                currency=new_currency,
                payment_date=new_date,
                base_currency=user.base_currency,
            )
            payment.exchange_rate = rate_data["exchange_rate"]
            payment.rate_from_currency = rate_data["rate_from_currency"]
            payment.rate_to_currency = rate_data["rate_to_currency"]
            payment.rate_date = rate_data["rate_date"]
            payment.converted_amount = rate_data["converted_amount"]
        elif "amount" in updates and payment.exchange_rate:
            if payment.rate_from_currency == payment.currency:
                payment.converted_amount = new_amount / payment.exchange_rate
            else:
                payment.converted_amount = new_amount * payment.exchange_rate

        if "payment_method" in updates:
            payment.payment_method = updates["payment_method"]

        payment.amount = new_amount
        payment.currency = new_currency
        payment.payment_date = new_date

        return self.payment_history_repository.save(payment)

    def delete_payment(self, user_id: int, payment_id: int) -> None:
        """支払履歴を削除する."""
        logger.info(
            "Starting deletion of payment_history_id=%s for user_id=%s",
            payment_id,
            user_id,
        )
        try:
            payment = self.payment_history_repository.find_by_id(payment_id)
            if not payment:
                msg = "Payment history not found"
                raise ResourceNotFoundError(msg)

            if payment.user_id != int(user_id):
                msg = "This payment history does not belong to the current user"
                raise ForbiddenError(msg)

            self.payment_history_repository.delete(payment)
            logger.info("Successfully deleted payment_history_id=%s", payment_id)
        except Exception as e:
            logger.exception(
                "Failed to delete payment_history_id=%s: %s", payment_id, str(e),
            )
            raise
