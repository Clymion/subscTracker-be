import pytest
from unittest.mock import MagicMock
from datetime import date

from app.services.payment_history_service import PaymentHistoryService
from app.repositories.payment_history_repository import PaymentHistoryRepository
from app.models.payment_history import PaymentHistory
from app.exceptions import ResourceNotFoundError, ForbiddenError, ValidationError
from app.repositories.user_repository import UserRepository
from app.repositories.subscription_repository import SubscriptionRepository
from app.services.exchange_rate_service import ExchangeRateService


@pytest.fixture
def mock_payment_history_repository():
    return MagicMock(spec=PaymentHistoryRepository)


@pytest.fixture
def mock_user_repository():
    return MagicMock(spec=UserRepository)


@pytest.fixture
def mock_subscription_repository():
    return MagicMock(spec=SubscriptionRepository)


@pytest.fixture
def mock_exchange_rate_service():
    return MagicMock(spec=ExchangeRateService)


@pytest.fixture
def service(
    mock_payment_history_repository,
    mock_user_repository,
    mock_subscription_repository,
    mock_exchange_rate_service,
):
    return PaymentHistoryService(
        session=MagicMock(),
        payment_history_repository=mock_payment_history_repository,
        user_repository=mock_user_repository,
        subscription_repository=mock_subscription_repository,
        exchange_rate_service=mock_exchange_rate_service,
    )


@pytest.fixture
def sample_payment_histories():
    return [
        PaymentHistory(
            payment_id=1,
            user_id=1,
            subscription_id=101,
            subscription_name="Netflix",
            payment_date=date(2023, 1, 1),
            amount=10.0,
            currency="USD",
            rate_from_currency="USD",
            rate_to_currency="JPY",
            rate_date=date(2023, 1, 1),
            payment_method="Credit Card",
        ),
        PaymentHistory(
            payment_id=2,
            user_id=1,
            subscription_id=102,
            subscription_name="Spotify",
            payment_date=date(2023, 2, 1),
            amount=5.0,
            currency="USD",
            rate_from_currency="USD",
            rate_to_currency="JPY",
            rate_date=date(2023, 2, 1),
            payment_method="PayPal",
        ),
    ]


class TestPaymentHistoryService:
    def test_get_payment_history_no_filters(self, service, mock_payment_history_repository, sample_payment_histories):
        # Arrange
        user_id = 1
        mock_payment_history_repository.find_all_by_user_id.return_value = sample_payment_histories
        mock_payment_history_repository.count_all_by_user_id.return_value = len(sample_payment_histories)

        # Act
        payments, total = service.get_payment_history(user_id, {}, "payment_date", "desc", 100, 0)

        # Assert
        assert len(payments) == 2
        assert total == 2
        mock_payment_history_repository.find_all_by_user_id.assert_called_once_with(user_id, {}, "payment_date", "desc", 100, 0)
        mock_payment_history_repository.count_all_by_user_id.assert_called_once_with(user_id, {})

    def test_get_payment_history_with_filters(self, service, mock_payment_history_repository, sample_payment_histories):
        # Arrange
        user_id = 1
        filters = {"subscription_id": 101, "start_date": date(2023, 1, 1)}
        mock_payment_history_repository.find_all_by_user_id.return_value = [sample_payment_histories[0]]
        mock_payment_history_repository.count_all_by_user_id.return_value = 1

        # Act
        payments, total = service.get_payment_history(user_id, filters, "payment_date", "desc", 100, 0)

        # Assert
        assert len(payments) == 1
        assert total == 1
        mock_payment_history_repository.find_all_by_user_id.assert_called_once_with(user_id, filters, "payment_date", "desc", 100, 0)
        mock_payment_history_repository.count_all_by_user_id.assert_called_once_with(user_id, filters)

    def test_create_payment_base_currency_success(
        self,
        service,
        mock_user_repository,
        mock_subscription_repository,
        mock_payment_history_repository,
        mock_exchange_rate_service,
    ):
        # Arrange
        user_id = 1
        mock_user = MagicMock()
        mock_user.base_currency = "USD"
        mock_user_repository.find_by_id.return_value = mock_user

        mock_subscription = MagicMock()
        mock_subscription.user_id = user_id
        mock_subscription.name = "Test Subscription"
        mock_subscription_repository.find_by_id.return_value = mock_subscription

        # Mock Identity Rate
        mock_rate = MagicMock()
        mock_rate.rate = 1.0
        mock_rate.from_currency = "USD"
        mock_rate.to_currency = "USD"
        mock_rate.date = date(2025, 1, 1)
        mock_exchange_rate_service.get_exchange_rate.return_value = (mock_rate, False)

        payment_data = {
            "subscription_id": 101,
            "payment_date": date(2025, 1, 1),
            "amount": 20.00,
            "currency": "USD",
            "payment_method": "credit_card",
        }
        
        # Act
        service.create_payment(user_id, payment_data)

        # Assert
        mock_payment_history_repository.save.assert_called_once()
        saved_payment: PaymentHistory = mock_payment_history_repository.save.call_args[0][0]
        
        assert saved_payment.user_id == user_id
        assert saved_payment.amount == 20.00
        assert saved_payment.currency == "USD"
        assert saved_payment.exchange_rate == 1.0
        assert saved_payment.converted_amount == 20.00

    def test_create_payment_foreign_currency_success(
        self,
        service,
        mock_user_repository,
        mock_subscription_repository,
        mock_payment_history_repository,
        mock_exchange_rate_service,
    ):
        # Arrange
        user_id = 1
        mock_user = MagicMock()
        mock_user.base_currency = "USD"
        mock_user_repository.find_by_id.return_value = mock_user

        mock_subscription = MagicMock()
        mock_subscription.user_id = user_id
        mock_subscription.name = "Test Subscription"
        mock_subscription_repository.find_by_id.return_value = mock_subscription
        
        mock_rate = MagicMock()
        mock_rate.rate = 150.0
        mock_rate.from_currency = "JPY"
        mock_rate.to_currency = "USD"
        mock_rate.date = date(2025, 1, 1)
        mock_exchange_rate_service.get_exchange_rate.return_value = (mock_rate, False)

        payment_data = {
            "subscription_id": 101,
            "payment_date": date(2025, 1, 1),
            "amount": 3000,
            "currency": "JPY",
            "payment_method": "credit_card",
        }
        
        # Act
        service.create_payment(user_id, payment_data)

        # Assert
        mock_payment_history_repository.save.assert_called_once()
        saved_payment: PaymentHistory = mock_payment_history_repository.save.call_args[0][0]
        
        assert saved_payment.currency == "JPY"
        assert saved_payment.exchange_rate == 150.0
        assert saved_payment.converted_amount == 20.0 # 3000 / 150
        assert saved_payment.rate_from_currency == "JPY"
        assert saved_payment.rate_to_currency == "USD"

    def test_create_payment_raises_resource_not_found_for_bad_subscription(
        self,
        service,
        mock_user_repository,
        mock_subscription_repository,
    ):
        # Arrange
        user_id = 1
        mock_user_repository.find_by_id.return_value = MagicMock()
        mock_subscription_repository.find_by_id.return_value = None # No subscription found

        payment_data = {"subscription_id": 999}

        # Act & Assert
        with pytest.raises(ResourceNotFoundError, match="Subscription not found"):
            service.create_payment(user_id, payment_data)

    def test_create_payment_raises_forbidden_for_other_user_subscription(
        self,
        service,
        mock_user_repository,
        mock_subscription_repository,
    ):
        # Arrange
        user_id = 1 # The user making the request
        other_user_id = 2 # The owner of the subscription
        mock_user_repository.find_by_id.return_value = MagicMock()

        mock_subscription = MagicMock()
        mock_subscription.user_id = other_user_id # Belongs to a different user
        mock_subscription_repository.find_by_id.return_value = mock_subscription

        payment_data = {"subscription_id": 101}

        # Act & Assert
        with pytest.raises(ForbiddenError, match="This subscription does not belong to the current user"):
            service.create_payment(user_id, payment_data)

    def test_create_payment_raises_validation_error_for_missing_rate(
        self,
        service,
        mock_user_repository,
        mock_subscription_repository,
        mock_exchange_rate_service,
    ):
        # Arrange
        user_id = 1
        mock_user = MagicMock()
        mock_user.base_currency = "USD"
        mock_user_repository.find_by_id.return_value = mock_user

        mock_subscription = MagicMock()
        mock_subscription.user_id = user_id
        mock_subscription_repository.find_by_id.return_value = mock_subscription

        # Simulate that the exchange rate service can't find a rate
        mock_exchange_rate_service.get_exchange_rate.side_effect = ResourceNotFoundError

        payment_data = {
            "subscription_id": 101,
            "payment_date": date(2025, 1, 1),
            "amount": 1000,
            "currency": "JPY", # Foreign currency
        }

        # Act & Assert
        with pytest.raises(ValidationError, match="Exchange rate not found"):
            service.create_payment(user_id, payment_data)
