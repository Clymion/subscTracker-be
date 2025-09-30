"""
Subscription Service for business logic.

This module contains the business logic for managing user subscriptions,
including validation, CRUD operations, and payment date calculations.
"""

from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app.common.logging_setup import get_logger
from app.constants import ErrorMessages
from app.exceptions import (
    DuplicateSubscriptionError,
    SubscriptionNotFoundError,
    ValidationError,
)
from app.models.subscription import Subscription
from app.repositories.label_repository import LabelRepository
from app.repositories.subscription_repository import SubscriptionRepository

logger = get_logger(__name__)


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
        # frequencyキーがあればpayment_frequencyにマッピングする
        if "frequency" in data:
            data["payment_frequency"] = data.pop("frequency")

        name = data.get("name")
        if self.subscription_repository.find_by_user_and_name(user_id, name):
            raise DuplicateSubscriptionError(ErrorMessages.DUPLICATE_SUBSCRIPTION)

        # labelsを除いたデータをSubscriptionモデルに渡す
        label_ids = data.pop("labels", [])
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
            logger.exception(e)
            raise ValidationError(str(e)) from e

        # ラベルの処理
        if label_ids:
            new_labels = []
            for label_id in label_ids:
                try:
                    # 文字列で送られてきたIDを整数に変換
                    l_id = int(label_id)
                except (ValueError, TypeError):
                    raise ValidationError(
                        f"Invalid label ID format: '{label_id}'. Please provide a numeric ID.",
                    )

                label = self.label_repository.find_by_id(l_id)
                # ラベルが存在するか、そして自分のものかを確認するのだ
                if not label or label.user_id != user_id:
                    raise ValidationError(
                        f"Label with ID {l_id} not found or access denied.",
                    )
                new_labels.append(label)
            subscription.labels = new_labels

        return self.subscription_repository.save(subscription)

    def update_subscription(
        self,
        user_id: int,
        subscription_id: int,
        data: dict[str, Any],
    ) -> Subscription:
        """
        Update an existing subscription.
        """
        subscription = self.get_subscription(user_id, subscription_id)

        update_data = data.get("subscription", data)

        # 日付関連のキーをリストアップ
        date_keys = ["initial_payment_date", "next_payment_date"]
        for key in date_keys:
            if key in update_data and isinstance(update_data[key], str):
                try:
                    # ISOフォーマットの文字列をdateオブジェクトに変換するのだ
                    update_data[key] = datetime.fromisoformat(update_data[key]).date()
                except ValueError:
                    raise ValidationError(
                        f"Invalid date format for {key}. Use YYYY-MM-DD.",
                    )

        # ラベルの更新
        label_ids = update_data.pop("labels", None)
        if label_ids is not None:
            new_labels = []
            logger.debug(label_ids)
            for label_id in label_ids:
                try:
                    l_id = int(label_id)
                    logger.debug(f"Processing label ID: {l_id}")
                except (ValueError, TypeError):
                    raise ValidationError(
                        f"Invalid label ID format: '{label_id}'. Please provide a numeric ID.",
                    )
                label = self.label_repository.find_by_id(l_id)
                if not label or label.user_id != user_id:
                    raise ValidationError(
                        f"Label with ID {label_id} not found or access denied.",
                    )
                new_labels.append(label)
            subscription.labels = new_labels

        # 新しい名前が他のサブスクリプションと重複しないかチェック
        new_name = update_data.get("name")
        if new_name and new_name.lower() != subscription.name.lower():
            existing = self.subscription_repository.find_by_user_and_name(
                user_id,
                new_name,
            )
            if existing and existing.subscription_id != subscription_id:
                raise DuplicateSubscriptionError(ErrorMessages.DUPLICATE_SUBSCRIPTION)

        # 残りのデータを更新
        for key, value in update_data.items():
            if key in ["id", "subscription_id", "user_id", "created_at", "updated_at"]:
                continue
            if hasattr(subscription, key):
                setattr(subscription, key, value)

        try:
            # 更新後にバリデーション
            subscription.validate_price()
            subscription.validate_currency()
            subscription.validate_status()

            # 支払頻度か初回支払日が変更された場合は次回支払日を再計算
            if (
                "payment_frequency" in update_data
                or "initial_payment_date" in update_data
            ):
                # この時点では initial_payment_date は必ず date オブジェクトなのだ
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
