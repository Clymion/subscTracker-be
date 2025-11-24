import pytest
from unittest.mock import MagicMock
from datetime import date

from app.services.payment_history_service import PaymentHistoryService
from app.repositories.payment_history_repository import PaymentHistoryRepository
from app.models.payment_history import PaymentHistory


@pytest.fixture
def mock_repository():
    return MagicMock(spec=PaymentHistoryRepository)


@pytest.fixture
def service(mock_repository):
    return PaymentHistoryService(session=MagicMock(), payment_history_repository=mock_repository)


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
    def test_get_payment_history_no_filters(self, service, mock_repository, sample_payment_histories):
        # Arrange
        user_id = 1
        mock_repository.find_all_by_user_id.return_value = sample_payment_histories
        mock_repository.count_all_by_user_id.return_value = len(sample_payment_histories)

        # Act
        payments, total = service.get_payment_history(user_id, {}, "payment_date", "desc", 100, 0)

        # Assert
        assert len(payments) == 2
        assert total == 2
        mock_repository.find_all_by_user_id.assert_called_once_with(user_id, {}, "payment_date", "desc", 100, 0)
        mock_repository.count_all_by_user_id.assert_called_once_with(user_id, {})

    def test_get_payment_history_with_filters(self, service, mock_repository, sample_payment_histories):
        # Arrange
        user_id = 1
        filters = {"subscription_id": 101, "start_date": date(2023, 1, 1)}
        mock_repository.find_all_by_user_id.return_value = [sample_payment_histories[0]]
        mock_repository.count_all_by_user_id.return_value = 1

        # Act
        payments, total = service.get_payment_history(user_id, filters, "payment_date", "desc", 100, 0)

        # Assert
        assert len(payments) == 1
        assert total == 1
        mock_repository.find_all_by_user_id.assert_called_once_with(user_id, filters, "payment_date", "desc", 100, 0)
        mock_repository.count_all_by_user_id.assert_called_once_with(user_id, filters)
