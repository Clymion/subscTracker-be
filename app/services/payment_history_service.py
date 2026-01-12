from typing import Any
from datetime import date, datetime

from sqlalchemy.orm import Session

from app.models.payment_history import PaymentHistory
from app.models.user import User
from app.models.subscription import Subscription
from app.repositories.payment_history_repository import PaymentHistoryRepository
from app.repositories.user_repository import UserRepository
from app.repositories.subscription_repository import SubscriptionRepository
from app.services.exchange_rate_service import ExchangeRateService
from app.exceptions import ValidationError, ResourceNotFoundError, ForbiddenError


class PaymentHistoryService:
    def __init__(
        self,
        session: Session,
        payment_history_repository: PaymentHistoryRepository,
        user_repository: UserRepository,
        subscription_repository: SubscriptionRepository,
        exchange_rate_service: ExchangeRateService,
    ) -> None:
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

    def create_payment(self, user_id: int, payment_data: dict) -> PaymentHistory:
        """
        新しい支払い履歴を作成し、DBに保存する
        """
        user = self.user_repository.find_by_id(user_id)
        if not user:
            raise ResourceNotFoundError("User not found")

        # First, check if the subscription exists at all
        subscription = self.subscription_repository.find_by_id(
            payment_data["subscription_id"]
        )
        if not subscription:
            raise ResourceNotFoundError("Subscription not found")

        # Then, check if it belongs to the user
        if subscription.user_id != int(user_id):
            raise ForbiddenError("This subscription does not belong to the current user")

        payment_date_obj = payment_data["payment_date"]
        payment_currency = payment_data["currency"]
        amount = payment_data["amount"]

        rate_from_currency = None
        rate_to_currency = None
        rate_date = None
        exchange_rate = None
        converted_amount = amount

        if payment_currency != user.base_currency:
            try:
                rate = self.exchange_rate_service.get_exchange_rate(
                    payment_date_obj,
                    from_currency=payment_currency,
                    to_currency=user.base_currency,
                )
            except ResourceNotFoundError:
                raise ValidationError(
                    f"Exchange rate not found for {payment_currency} to {user.base_currency} on {payment_date_obj}"
                )
            
            rate_from_currency = payment_currency
            rate_to_currency = user.base_currency
            rate_date = payment_date_obj
            exchange_rate = rate.rate
            converted_amount = amount / rate.rate

        payment = PaymentHistory(
            user_id=user_id,
            subscription_id=payment_data["subscription_id"],
            subscription_name=subscription.name,
            payment_date=payment_date_obj,
            amount=amount,
            currency=payment_currency,
            rate_from_currency=rate_from_currency,
            rate_to_currency=rate_to_currency,
            rate_date=rate_date,
            exchange_rate=exchange_rate,
            converted_amount=converted_amount,
            payment_method=payment_data["payment_method"],
        )
        return self.payment_history_repository.save(payment)
