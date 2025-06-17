"""
Subscription Service for business logic.

This module contains the business logic for managing user subscriptions,
including validation, CRUD operations, and payment date calculations.
"""

from typing import Any

from sqlalchemy.orm import Session

from app.constants import ErrorMessages
from app.exceptions import (
    DuplicateSubscriptionError,
    SubscriptionNotFoundError,
    ValidationError,
)

# LabelモデルとLabelNotFoundErrorをインポートするのだ
from app.models.label import Label
from app.models.subscription import Subscription
from app.repositories.label_repository import (
    LabelRepository,
)  # ラベルリポジトリもインポート
from app.repositories.subscription_repository import SubscriptionRepository


class SubscriptionService:
    """Service for subscription-related business logic."""

    def __init__(self, session: Session) -> None:
        """
        Initialize the service with a database session.

        Args:
            session: The SQLAlchemy Session object.
        """
        self.session = session
        self.subscription_repository = SubscriptionRepository(session)
        # LabelRepositoryも初期化する
        self.label_repository = LabelRepository(session)

    def get_subscription(self, user_id: int, subscription_id: int) -> Subscription:
        """
        Get a single subscription by ID, ensuring user ownership.

        Raises:
            SubscriptionNotFoundError: If subscription not found or user does not have permission.
        """
        subscription = self.subscription_repository.find_by_id(subscription_id)
        if not subscription or subscription.user_id != user_id:
            raise SubscriptionNotFoundError(ErrorMessages.SUBSCRIPTION_NOT_FOUND)
        return subscription

    def get_subscriptions_by_user(
        self,
        user_id: int,
        filters: dict[str, Any] | None = None,
        sort_by: str | None = None,
        sort_order: str = "asc",
        limit: int = 100,
        offset: int = 0,
    ) -> list[Subscription]:
        """Get a list of subscriptions for a user with optional filters."""
        filters = filters or {}
        return self.subscription_repository.find_all_by_user_id(
            user_id,
            filters,
            sort_by,
            sort_order,
            limit,
            offset,
        )

    def create_subscription(self, user_id: int, data: dict[str, Any]) -> Subscription:
        """
        Create a new subscription with validation.

        Raises:
            DuplicateSubscriptionError:
                If a subscription with the same name already exists for the user.
            ValidationError: If input data is invalid.
        """
        name = data.get("name")
        if self.subscription_repository.find_by_user_and_name(user_id, name):
            raise DuplicateSubscriptionError(ErrorMessages.DUPLICATE_SUBSCRIPTION)

        try:
            subscription = Subscription(user_id=user_id, **data)
            # モデルのバリデーションを実行
            subscription.validate_price()
            subscription.validate_currency()
            subscription.validate_status()
            subscription.validate_payment_frequency()
            # 次回支払日を計算
            subscription.next_payment_date = subscription.calculate_next_payment_date(
                from_date=subscription.initial_payment_date,
            )
            subscription.validate_dates()
        except (ValueError, TypeError) as e:
            raise ValidationError(str(e)) from e

        return self.subscription_repository.save(subscription)

    def update_subscription(
        self,
        user_id: int,
        subscription_id: int,
        data: dict[str, Any],
    ) -> Subscription:
        """
        Update an existing subscription.

        Raises:
            SubscriptionNotFoundError:
                If the subscription is not found or user does not have permission.
            DuplicateSubscriptionError: If the new name conflicts with an existing subscription.
            ValidationError: If update data is invalid.
        """
        subscription = self.get_subscription(user_id, subscription_id)

        # ラベルの更新を先に処理する
        if "labels" in data:
            label_ids = data.pop("labels", [])
            new_labels = []
            for label_id in label_ids:
                label = self.label_repository.find_by_id(label_id)
                if not label or label.user_id != user_id:
                    raise ValidationError(
                        f"Label with ID {label_id} not found or access denied."
                    )
                new_labels.append(label)
            subscription.labels = new_labels

        # 新しい名前が他のサブスクリプションと重複しないかチェック
        new_name = data.get("name")
        if new_name and new_name.lower() != subscription.name.lower():
            existing = self.subscription_repository.find_by_user_and_name(
                user_id,
                new_name,
            )
            if existing and existing.subscription_id != subscription_id:
                raise DuplicateSubscriptionError(ErrorMessages.DUPLICATE_SUBSCRIPTION)

        # 残りのデータを更新
        for key, value in data.items():
            if hasattr(subscription, key):
                setattr(subscription, key, value)

        try:
            # 更新後にバリデーション
            subscription.validate_price()
            subscription.validate_currency()
            subscription.validate_status()
            # 支払頻度が変更された場合は次回支払日を再計算
            if "payment_frequency" in data or "initial_payment_date" in data:
                subscription.next_payment_date = (
                    subscription.calculate_next_payment_date(
                        from_date=subscription.initial_payment_date,
                    )
                )
            subscription.validate_dates()
        except (ValueError, TypeError) as e:
            raise ValidationError(str(e)) from e

        return self.subscription_repository.save(subscription)

    def delete_subscription(self, user_id: int, subscription_id: int) -> None:
        """
        Delete a subscription (hard delete).

        Raises:
            SubscriptionNotFoundError:
                If the subscription is not found or user does not have permission.
        """
        subscription = self.get_subscription(user_id, subscription_id)
        self.subscription_repository.delete(subscription)
