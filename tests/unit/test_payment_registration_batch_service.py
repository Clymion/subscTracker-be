from datetime import date
from unittest.mock import MagicMock, patch

import pytest

from app.common.result import Result
from app.constants import CurrencyConstants, PaymentFrequency, SubscriptionStatus
from app.models.payment_history import PaymentHistory
from app.models.subscription import Subscription
from app.models.user import User
from app.services.payment_registration_batch_service import (
    BatchSummary,
    PaymentRegistrationBatchService,
)

# Since the service now instantiates its own dependencies,
# we need to patch the classes themselves.
@pytest.fixture(autouse=True)
def mock_subscription_repo_class():
    with patch(
        "app.services.payment_registration_batch_service.SubscriptionRepository"
    ) as mock:
        yield mock


@pytest.fixture
def mock_subscription_repo(mock_subscription_repo_class):
    return mock_subscription_repo_class.return_value


@pytest.fixture(autouse=True)
def mock_payment_history_repo_class():
    with patch(
        "app.services.payment_registration_batch_service.PaymentHistoryRepository"
    ) as mock:
        yield mock


@pytest.fixture
def mock_payment_history_repo(mock_payment_history_repo_class):
    return mock_payment_history_repo_class.return_value


@pytest.fixture(autouse=True)
def mock_exchange_rate_repo_class():
    with patch(
        "app.services.payment_registration_batch_service.ExchangeRateRepository"
    ) as mock:
        yield mock


@pytest.fixture(autouse=True)
def mock_exchange_rate_service_class():
    with patch(
        "app.services.payment_registration_batch_service.ExchangeRateService"
    ) as mock:
        yield mock


@pytest.fixture
def mock_exchange_rate_service(mock_exchange_rate_service_class):
    return mock_exchange_rate_service_class.return_value


@pytest.fixture
def mock_logger():
    with patch("app.services.payment_registration_batch_service.logger") as mock_log:
        yield mock_log


@pytest.fixture
def mock_db():
    mock_db_instance = MagicMock()
    # The session itself will be mocked to control transaction behavior
    mock_db_instance.session = MagicMock()
    return mock_db_instance


@pytest.fixture
def service(mock_db):
    return PaymentRegistrationBatchService(db_instance=mock_db)


@pytest.fixture
def sample_user():
    return User(
        user_id=1,
        username="testuser",
        email="test@example.com",
        base_currency=CurrencyConstants.JPY,
    )


@pytest.fixture
def due_subscription(sample_user):
    return Subscription(
        subscription_id=101,
        user_id=sample_user.user_id,
        user=sample_user,
        name="Test Subscription",
        price=10.0,
        currency=CurrencyConstants.USD,
        payment_frequency=PaymentFrequency.MONTHLY,
        initial_payment_date=date(2024, 1, 15),
        next_payment_date=date(2024, 2, 15),
        payment_method="credit_card",
        status=SubscriptionStatus.ACTIVE,
    )


@pytest.fixture
def due_subscription_for_backfill(sample_user):
    return Subscription(
        subscription_id=102,
        user_id=sample_user.user_id,
        user=sample_user,
        name="Backfill Service",
        price=20.0,
        currency=CurrencyConstants.USD,
        payment_frequency=PaymentFrequency.MONTHLY,
        initial_payment_date=date(2023, 10, 1),
        next_payment_date=None,
        payment_method="bank_transfer",
        status=SubscriptionStatus.ACTIVE,
    )


class TestPaymentRegistrationBatchService:
    def test_execute_success_for_single_due_subscription(
        self,
        service,
        mock_subscription_repo,
        mock_payment_history_repo,
        mock_exchange_rate_service,
        due_subscription,
    ):
        today = date(2024, 2, 20)
        next_due_date = date(2024, 3, 15)

        mock_subscription_repo.find_due_subscriptions.return_value = [due_subscription]
        mock_payment_history_repo.find_latest_by_subscription_id.return_value = PaymentHistory(
            payment_date=date(2024, 1, 15)
        )
        mock_exchange_rate_service.get_rate.return_value = Result.Ok(150.0)

        with patch("app.services.payment_registration_batch_service.date") as mock_date:
            mock_date.today.return_value = today
            result = service.execute()

        assert result.is_ok()
        summary = result.unwrap()
        assert summary.success == 1
        mock_subscription_repo.update_next_payment_date.assert_called_once_with(
            due_subscription, next_due_date
        )

    def test_execute_backfills_missing_payment_histories(
        self,
        service,
        mock_subscription_repo,
        mock_payment_history_repo,
        mock_exchange_rate_service,
        due_subscription_for_backfill,
    ):
        today = date(2024, 2, 20)
        next_due_date_after_backfill = date(2024, 3, 1)

        mock_subscription_repo.find_due_subscriptions.return_value = [
            due_subscription_for_backfill
        ]
        mock_payment_history_repo.find_latest_by_subscription_id.return_value = None
        mock_exchange_rate_service.get_rate.return_value = Result.Ok(160.0)

        with patch("app.services.payment_registration_batch_service.date") as mock_date:
            mock_date.today.return_value = today
            result = service.execute()

        assert result.is_ok()
        summary = result.unwrap()
        assert summary.success == 1
        mock_subscription_repo.update_next_payment_date.assert_called_once_with(
            due_subscription_for_backfill, next_due_date_after_backfill
        )

    def test_execute_rollback_on_failure(
        self, service, mock_db, mock_subscription_repo, mock_payment_history_repo, due_subscription
    ):
        today = date(2024, 2, 20)
        mock_subscription_repo.find_due_subscriptions.return_value = [due_subscription]
        mock_payment_history_repo.find_latest_by_subscription_id.return_value = None
        mock_payment_history_repo.bulk_save.side_effect = Exception("DB Error")

        with patch("app.services.payment_registration_batch_service.date") as mock_date:
            mock_date.today.return_value = today
            result = service.execute()

        assert result.is_ok()
        summary = result.unwrap()
        assert summary.failed == 1
        
        # Verify that rollback was called on the session mock
        mock_db.session.rollback.assert_called_once()
        mock_db.session.commit.assert_not_called()