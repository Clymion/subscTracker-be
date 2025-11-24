import pytest
from unittest.mock import MagicMock
from datetime import date

from app.models.payment_history import PaymentHistory
from app.repositories.payment_history_repository import PaymentHistoryRepository


@pytest.fixture
def mock_session():
    return MagicMock()


@pytest.fixture
def repository(mock_session):
    return PaymentHistoryRepository(mock_session)


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
        PaymentHistory(
            payment_id=3,
            user_id=2,
            subscription_id=103,
            subscription_name="YouTube Premium",
            payment_date=date(2023, 3, 1),
            amount=12.0,
            currency="JPY",
            rate_from_currency="JPY",
            rate_to_currency="JPY",
            rate_date=date(2023, 3, 1),
            payment_method="Credit Card",
        ),
    ]


class TestPaymentHistoryRepository:
    def test_find_all_by_user_id_no_filters(self, repository, mock_session, sample_payment_histories):
        # Arrange
        user_id = 1
        mock_query = mock_session.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.filter.return_value.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.all.return_value = [sample_payment_histories[0], sample_payment_histories[1]]

        # Act
        result = repository.find_all_by_user_id(user_id, {}, "payment_date", "asc", 10, 0)

        # Assert
        assert len(result) == 2
        assert result[0].payment_id == 1
        assert result[1].payment_id == 2
        mock_session.query.assert_called_once_with(PaymentHistory)
        mock_session.query.return_value.filter.assert_called_once()

    def test_find_all_by_user_id_with_subscription_id_filter(self, repository, mock_session, sample_payment_histories):
        # Arrange
        user_id = 1
        filters = {"subscription_id": 101}
        mock_query = mock_session.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.all.return_value = [sample_payment_histories[0]]

        # Act
        result = repository.find_all_by_user_id(user_id, filters, "payment_date", "asc", 10, 0)

        # Assert
        assert len(result) == 1
        assert result[0].payment_id == 1

    def test_find_all_by_user_id_with_date_range_filter(self, repository, mock_session, sample_payment_histories):
        # Arrange
        user_id = 1
        filters = {"start_date": date(2023, 1, 15), "end_date": date(2023, 2, 15)}
        mock_query = mock_session.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.filter.return_value.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.all.return_value = [sample_payment_histories[1]]

        # Act
        result = repository.find_all_by_user_id(user_id, filters, "payment_date", "asc", 10, 0)

        # Assert
        assert len(result) == 1
        assert result[0].payment_id == 2

    def test_find_all_by_user_id_with_currency_filter(self, repository, mock_session, sample_payment_histories):
        # Arrange
        user_id = 1
        filters = {"currency": "USD"}
        mock_query = mock_session.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.filter.return_value.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.all.return_value = [sample_payment_histories[0], sample_payment_histories[1]]

        # Act
        result = repository.find_all_by_user_id(user_id, filters, "payment_date", "asc", 10, 0)

        # Assert
        assert len(result) == 2
        assert result[0].payment_id == 1
        assert result[1].payment_id == 2

    def test_find_all_by_user_id_with_payment_method_filter(self, repository, mock_session, sample_payment_histories):
        # Arrange
        user_id = 1
        filters = {"payment_method": "Credit Card"}
        mock_query = mock_session.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.filter.return_value.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.all.return_value = [sample_payment_histories[0]]

        # Act
        result = repository.find_all_by_user_id(user_id, filters, "payment_date", "asc", 10, 0)

        # Assert
        assert len(result) == 1
        assert result[0].payment_id == 1

    def test_count_all_by_user_id_no_filters(self, repository, mock_session):
        # Arrange
        user_id = 1
        mock_query = mock_session.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.filter.return_value.filter.return_value = mock_query
        mock_query.count.return_value = 2

        # Act
        result = repository.count_all_by_user_id(user_id, {})

        # Assert
        assert result == 2
        mock_session.query.assert_called_once_with(PaymentHistory.payment_id)
        mock_session.query.return_value.filter.assert_called_once()

    def test_count_all_by_user_id_with_filter(self, repository, mock_session):
        # Arrange
        user_id = 1
        filters = {"subscription_id": 101}
        mock_query = mock_session.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.filter.return_value.filter.return_value = mock_query
        mock_query.count.return_value = 1

        # Act
        result = repository.count_all_by_user_id(user_id, filters)

        # Assert
        assert result == 1

    def test_find_by_id(self, repository, mock_session, sample_payment_histories):
        # Arrange
        payment_id = 1
        mock_query = mock_session.query.return_value
        mock_query.filter_by.return_value = mock_query
        mock_query.first.return_value = sample_payment_histories[0]

        # Act
        result = repository.find_by_id(payment_id)

        # Assert
        assert result.payment_id == payment_id
        mock_session.query.assert_called_once_with(PaymentHistory)
        mock_session.query.return_value.filter_by.assert_called_once_with(payment_id=payment_id)

    def test_save_new_payment_history(self, repository, mock_session):
        # Arrange
        new_payment = PaymentHistory(
            user_id=1,
            subscription_id=101,
            subscription_name="New Service",
            payment_date=date(2023, 4, 1),
            amount=15.0,
            currency="EUR",
            rate_from_currency="EUR",
            rate_to_currency="JPY",
            rate_date=date(2023, 4, 1),
            payment_method="Credit Card",
        )

        # Act
        repository.save(new_payment)

        # Assert
        mock_session.add.assert_called_once_with(new_payment)
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once_with(new_payment)

    def test_delete_payment_history(self, repository, mock_session, sample_payment_histories):
        # Arrange
        payment_to_delete = sample_payment_histories[0]

        # Act
        repository.delete(payment_to_delete)

        # Assert
        mock_session.delete.assert_called_once_with(payment_to_delete)
        mock_session.commit.assert_called_once()

    def test_bulk_save(self, repository, mock_session):
        # Arrange
        new_histories = [
            PaymentHistory(user_id=1, subscription_id=1, amount=10.0),
            PaymentHistory(user_id=1, subscription_id=1, amount=10.0),
        ]

        # Act
        repository.bulk_save(new_histories)

        # Assert
        mock_session.bulk_save_objects.assert_called_once_with(new_histories)
        mock_session.commit.assert_called_once()

    def test_find_latest_by_subscription_id(self, repository, mock_session):
        # Arrange
        subscription_id = 101
        latest_history = PaymentHistory(
            payment_id=4,
            subscription_id=subscription_id,
            payment_date=date(2023, 2, 1),
        )
        # The mock setup for the query chain
        mock_query = mock_session.query.return_value
        filtered_query = mock_query.filter_by.return_value
        ordered_query = filtered_query.order_by.return_value
        ordered_query.first.return_value = latest_history

        # Act
        result = repository.find_latest_by_subscription_id(subscription_id)

        # Assert
        assert result is not None
        assert result.payment_id == 4
        assert result.payment_date == date(2023, 2, 1)
        # Verify the query was constructed correctly
        mock_session.query.assert_called_with(PaymentHistory)
        mock_query.filter_by.assert_called_once_with(subscription_id=subscription_id)
        # Ensure it's ordering by payment_date descending
        filtered_query.order_by.assert_called_once()
        ordered_query.first.assert_called_once()
