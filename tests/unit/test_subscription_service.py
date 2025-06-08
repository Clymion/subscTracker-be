"""
Unit tests for SubscriptionService.

Tests the business logic for subscription management, including CRUD operations,
validation, and business rules enforcement, following the test list from
docs/test-list/subscription-service.md.
"""

from collections.abc import Generator
from datetime import date
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from app.constants import ErrorMessages
from app.exceptions import (
    DuplicateSubscriptionError,
    SubscriptionNotFoundError,
    ValidationError,
)
from app.models.subscription import Subscription
from app.services.subscription_service import SubscriptionService
from tests.helpers import (
    make_and_save_subscription,
    make_and_save_user,
    make_subscription,
)


@pytest.fixture
def mock_subscription_repo() -> MagicMock:
    """Fixture to create a mock SubscriptionRepository."""
    return MagicMock()


@pytest.fixture
def subscription_service(
    clean_db: Generator[Session, None, None],
    mock_subscription_repo: MagicMock,
) -> SubscriptionService:
    """Fixture to create a SubscriptionService instance with a mock repository."""
    service = SubscriptionService(session=clean_db)
    service.subscription_repository = mock_subscription_repo
    return service


@pytest.mark.unit
class TestSubscriptionServiceCreate:
    """Test cases for the create_subscription method."""

    def test_create_subscription_with_valid_data(
        self,
        subscription_service: SubscriptionService,
        mock_subscription_repo: MagicMock,
        clean_db: Generator[Session, None, None],
    ):
        """
        Test that a subscription is created successfully with valid data.
        """
        # Arrange
        user = make_and_save_user(clean_db)
        subscription_data = {
            "name": "Netflix",
            "price": 15.99,
            "currency": "USD",
            "payment_frequency": "monthly",
            "initial_payment_date": date(2024, 1, 1),
            "payment_method": "credit_card",
            "status": "active",
        }
        mock_subscription_repo.find_by_user_and_name.return_value = None
        mock_subscription_repo.save.side_effect = lambda sub: sub

        # Act
        new_subscription = subscription_service.create_subscription(
            user.user_id,
            subscription_data,
        )

        # Assert
        assert new_subscription is not None
        assert new_subscription.name == "Netflix"
        assert new_subscription.user_id == user.user_id
        assert new_subscription.status == "active"
        # サービスのロジックでnext_payment_dateが計算されることを確認
        assert new_subscription.next_payment_date is not None
        mock_subscription_repo.find_by_user_and_name.assert_called_once_with(
            user.user_id,
            "Netflix",
        )
        mock_subscription_repo.save.assert_called_once()

    def test_create_subscription_with_duplicate_name_raises_error(
        self,
        subscription_service: SubscriptionService,
        mock_subscription_repo: MagicMock,
        clean_db: Generator[Session, None, None],
    ):
        """
        Test that creating a subscription with a duplicate name for the same user

        raises DuplicateSubscriptionError.
        """
        # Arrange
        user = make_and_save_user(clean_db)
        subscription_data = {"name": "Netflix"}
        # モックリポジトリが既存のサブスクリプションを返すように設定
        mock_subscription_repo.find_by_user_and_name.return_value = Subscription(
            user_id=user.user_id,
            name="Netflix",
        )

        # Act & Assert
        with pytest.raises(
            DuplicateSubscriptionError,
            match=ErrorMessages.DUPLICATE_SUBSCRIPTION,
        ):
            subscription_service.create_subscription(user.user_id, subscription_data)
        mock_subscription_repo.save.assert_not_called()

    @pytest.mark.parametrize(
        ("field", "value", "error_message"),
        [
            ("price", -10, ErrorMessages.PRICE_MUST_BE_POSITIVE),
            ("currency", "EUR", ErrorMessages.UNSUPPORTED_CURRENCY),
            ("status", "invalid_status", ErrorMessages.INVALID_STATUS),
            ("payment_frequency", "weekly", ErrorMessages.INVALID_PAYMENT_FREQUENCY),
        ],
    )
    def test_create_subscription_with_invalid_data_raises_validation_error(
        self,
        subscription_service: SubscriptionService,
        mock_subscription_repo: MagicMock,
        clean_db: Generator[Session, None, None],
        field: str,
        value: any,
        error_message: str,
    ):
        """
        Test that creating a subscription with invalid data raises ValidationError.
        """
        # Arrange
        user = make_and_save_user(clean_db)
        subscription_data = {
            "name": "Test Service",
            "price": 9.99,
            "currency": "USD",
            "payment_frequency": "monthly",
            "initial_payment_date": date(2024, 1, 1),
            "payment_method": "credit_card",
            "status": "active",
        }
        subscription_data[field] = value
        mock_subscription_repo.find_by_user_and_name.return_value = None

        # Act & Assert
        with pytest.raises(ValidationError, match=error_message):
            subscription_service.create_subscription(user.user_id, subscription_data)
        mock_subscription_repo.save.assert_not_called()


@pytest.mark.unit
class TestSubscriptionServiceGet:
    """Test cases for getting subscriptions."""

    def test_get_subscription_by_id_for_owner(
        self,
        subscription_service: SubscriptionService,
        mock_subscription_repo: MagicMock,
        clean_db: Generator[Session, None, None],
    ):
        """
        Test that a user can retrieve their own subscription.
        """
        # Arrange
        user = make_and_save_user(clean_db)
        subscription = make_subscription(user_id=user.user_id)
        mock_subscription_repo.find_by_id.return_value = subscription

        # Act
        found_subscription = subscription_service.get_subscription(
            user.user_id,
            subscription.subscription_id,
        )

        # Assert
        assert found_subscription is not None
        assert found_subscription.user_id == user.user_id
        mock_subscription_repo.find_by_id.assert_called_once_with(
            subscription.subscription_id,
        )

    def test_get_subscription_raises_not_found_for_non_existent(
        self,
        subscription_service: SubscriptionService,
        mock_subscription_repo: MagicMock,
        clean_db: Generator[Session, None, None],
    ):
        """
        Test that SubscriptionNotFoundError is raised for a non-existent subscription.
        """
        # Arrange
        user = make_and_save_user(clean_db)
        non_existent_id = 999
        mock_subscription_repo.find_by_id.return_value = None

        # Act & Assert
        with pytest.raises(SubscriptionNotFoundError):
            subscription_service.get_subscription(user.user_id, non_existent_id)

    def test_get_subscription_raises_not_found_for_other_user(
        self,
        subscription_service: SubscriptionService,
        mock_subscription_repo: MagicMock,
        clean_db: Generator[Session, None, None],
    ):
        """
        Test that SubscriptionNotFoundError is raised when trying to access

        another user's subscription.
        """
        # Arrange
        owner_user = make_and_save_user(
            clean_db, username="owner", email="owner@test.com",
        )
        other_user = make_and_save_user(
            clean_db, username="other", email="other@test.com",
        )
        subscription = make_and_save_subscription(clean_db, user_id=owner_user.user_id)
        mock_subscription_repo.find_by_id.return_value = subscription

        # Act & Assert
        with pytest.raises(SubscriptionNotFoundError):
            subscription_service.get_subscription(
                other_user.user_id,
                subscription.subscription_id,
            )

    def test_get_subscriptions_by_user(
        self,
        subscription_service: SubscriptionService,
        mock_subscription_repo: MagicMock,
        clean_db: Generator[Session, None, None],
    ):
        """
        Test retrieving all subscriptions for a specific user.
        """
        # Arrange
        user = make_and_save_user(clean_db)
        subscriptions_list = [
            make_and_save_subscription(clean_db, user_id=user.user_id, name="Sub 1"),
            make_and_save_subscription(clean_db, user_id=user.user_id, name="Sub 2"),
        ]
        mock_subscription_repo.find_all_by_user_id.return_value = subscriptions_list

        # Act
        result = subscription_service.get_subscriptions_by_user(user.user_id)

        # Assert
        assert len(result) == 2
        mock_subscription_repo.find_all_by_user_id.assert_called_once_with(
            user.user_id, {}, None, "asc", 100, 0,
        )


@pytest.mark.unit
class TestSubscriptionServiceUpdate:
    """Test cases for updating subscriptions."""

    def test_update_subscription_success(
        self,
        subscription_service: SubscriptionService,
        mock_subscription_repo: MagicMock,
        clean_db: Generator[Session, None, None],
    ):
        """
        Test that a subscription is updated successfully with valid data.
        """
        # Arrange
        user = make_and_save_user(clean_db)
        subscription = make_subscription(user_id=user.user_id, name="Old Name")
        update_data = {"name": "New Name", "price": 20.0}

        mock_subscription_repo.find_by_id.return_value = subscription
        mock_subscription_repo.find_by_user_and_name.return_value = None
        mock_subscription_repo.save.side_effect = lambda sub: sub

        # Act
        updated_subscription = subscription_service.update_subscription(
            user.user_id,
            subscription.subscription_id,
            update_data,
        )

        # Assert
        assert updated_subscription.name == "New Name"
        assert updated_subscription.price == 20.0
        mock_subscription_repo.save.assert_called_once()

    def test_update_subscription_raises_not_found(
        self,
        subscription_service: SubscriptionService,
        mock_subscription_repo: MagicMock,
        clean_db: Generator[Session, None, None],
    ):
        """
        Test that updating a non-existent subscription raises SubscriptionNotFoundError.
        """
        # Arrange
        user = make_and_save_user(clean_db)
        non_existent_id = 999
        mock_subscription_repo.find_by_id.return_value = None

        # Act & Assert
        with pytest.raises(SubscriptionNotFoundError):
            subscription_service.update_subscription(user.user_id, non_existent_id, {})

    def test_update_subscription_to_duplicate_name_raises_error(
        self,
        subscription_service: SubscriptionService,
        mock_subscription_repo: MagicMock,
        clean_db: Generator[Session, None, None],
    ):
        """
        Test that updating a subscription to a name that

        already exists for the user raises DuplicateSubscriptionError.
        """
        # Arrange
        user = make_and_save_user(clean_db)
        sub1 = make_and_save_subscription(clean_db, user_id=user.user_id, name="Sub 1")
        sub2 = make_and_save_subscription(clean_db, user_id=user.user_id, name="Sub 2")
        update_data = {"name": "Sub 2"}

        mock_subscription_repo.find_by_id.return_value = sub1
        mock_subscription_repo.find_by_user_and_name.return_value = sub2

        # Act & Assert
        with pytest.raises(DuplicateSubscriptionError):
            subscription_service.update_subscription(
                user.user_id,
                sub1.subscription_id,
                update_data,
            )


@pytest.mark.unit
class TestSubscriptionServiceDelete:
    """Test cases for deleting subscriptions."""

    def test_delete_subscription_success(
        self,
        subscription_service: SubscriptionService,
        mock_subscription_repo: MagicMock,
        clean_db: Generator[Session, None, None],
    ):
        """
        Test that a subscription is deleted successfully.
        """
        # Arrange
        user = make_and_save_user(clean_db)
        subscription = make_subscription(user_id=user.user_id)
        mock_subscription_repo.find_by_id.return_value = subscription

        # Act
        subscription_service.delete_subscription(
            user.user_id,
            subscription.subscription_id,
        )

        # Assert
        mock_subscription_repo.find_by_id.assert_called_once_with(
            subscription.subscription_id,
        )
        mock_subscription_repo.delete.assert_called_once_with(subscription)

    def test_delete_subscription_raises_not_found(
        self,
        subscription_service: SubscriptionService,
        mock_subscription_repo: MagicMock,
        clean_db: Generator[Session, None, None],
    ):
        """
        Test that deleting a non-existent subscription raises SubscriptionNotFoundError.
        """
        # Arrange
        user = make_and_save_user(clean_db)
        non_existent_id = 999
        mock_subscription_repo.find_by_id.return_value = None

        # Act & Assert
        with pytest.raises(SubscriptionNotFoundError):
            subscription_service.delete_subscription(user.user_id, non_existent_id)
        mock_subscription_repo.delete.assert_not_called()

    def test_delete_subscription_for_other_user_raises_not_found(
        self,
        subscription_service: SubscriptionService,
        mock_subscription_repo: MagicMock,
        clean_db: Generator[Session, None, None],
    ):
        """
        Test that deleting another user's subscription raises SubscriptionNotFoundError.
        """
        # Arrange
        owner_user = make_and_save_user(
            clean_db, username="owner", email="owner@test.com",
        )
        other_user = make_and_save_user(
            clean_db, username="other", email="other@test.com",
        )
        subscription = make_subscription(user_id=owner_user.user_id)
        mock_subscription_repo.find_by_id.return_value = subscription

        # Act & Assert
        with pytest.raises(SubscriptionNotFoundError):
            subscription_service.delete_subscription(
                other_user.user_id,
                subscription.subscription_id,
            )
        mock_subscription_repo.delete.assert_not_called()
