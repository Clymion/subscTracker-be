from datetime import date, timedelta
from unittest.mock import MagicMock

import pytest

from app.models.label import Label
from app.models.subscription import Subscription
from app.models.user import User
from app.repositories.subscription_repository import SubscriptionRepository




@pytest.fixture
def subscription_repository(mock_session):
    return SubscriptionRepository(mock_session)


@pytest.fixture
def sample_user():
    return User(user_id=1, username="testuser", email="test@example.com")


@pytest.fixture
def sample_subscriptions(sample_user):
    today = date.today()
    return [
        Subscription(
            subscription_id=1,
            user_id=sample_user.user_id,
            name="Netflix",
            price=10.0,
            currency="USD",
            initial_payment_date=today - timedelta(days=30),
            next_payment_date=today,
            payment_frequency="monthly",
            payment_method="credit_card",
            status="active",
        ),
        Subscription(
            subscription_id=2,
            user_id=sample_user.user_id,
            name="Spotify",
            price=5.0,
            currency="USD",
            initial_payment_date=today - timedelta(days=60),
            next_payment_date=today + timedelta(days=10),
            payment_frequency="monthly",
            payment_method="paypal",
            status="active",
        ),
        Subscription(
            subscription_id=3,
            user_id=sample_user.user_id,
            name="Hulu",
            price=12.0,
            currency="JPY",
            initial_payment_date=today - timedelta(days=90),
            next_payment_date=today - timedelta(days=5),
            payment_frequency="yearly",
            payment_method="credit_card",
            status="active",
        ),
        Subscription(
            subscription_id=4,
            user_id=sample_user.user_id,
            name="Paused Service",
            price=8.0,
            currency="USD",
            initial_payment_date=today - timedelta(days=10),
            next_payment_date=today + timedelta(days=20),
            payment_frequency="monthly",
            payment_method="credit_card",
            status="paused",
        ),
    ]


class TestSubscriptionRepository:
    def test_find_by_id(
        self, subscription_repository, mock_session, sample_subscriptions
    ):
        mock_session.query.return_value.filter_by.return_value.first.return_value = (
            sample_subscriptions[0]
        )
        subscription = subscription_repository.find_by_id(1)
        assert subscription.subscription_id == 1

    def test_find_by_user_and_name(
        self,
        subscription_repository,
        mock_session,
        sample_subscriptions,
        sample_user,
    ):
        mock_session.query.return_value.filter.return_value.first.return_value = (
            sample_subscriptions[0]
        )
        subscription = subscription_repository.find_by_user_and_name(
            sample_user.user_id,
            "Netflix",
        )
        assert subscription.name == "Netflix"

    def test_find_all_by_user_id(
        self,
        subscription_repository,
        mock_session,
        sample_subscriptions,
        sample_user,
    ):
        mock_query = mock_session.query.return_value
        mock_query.filter.return_value.order_by.return_value.limit.return_value.offset.return_value.all.return_value = (
            sample_subscriptions
        )
        subscriptions = subscription_repository.find_all_by_user_id(
            sample_user.user_id,
            {},
            "created_at",
            "asc",
            10,
            0,
        )
        assert len(subscriptions) == 4

    def test_count_all_by_user_id(
        self,
        subscription_repository,
        mock_session,
        sample_user,
    ):
        mock_session.query.return_value.filter.return_value.count.return_value = 4
        count = subscription_repository.count_all_by_user_id(sample_user.user_id, {})
        assert count == 4

    def test_save_new_subscription(
        self,
        subscription_repository,
        mock_session,
        sample_user,
    ):
        new_sub = Subscription(
            user_id=sample_user.user_id,
            name="New Service",
            price=100.0,
            currency="JPY",
            initial_payment_date=date.today(),
            next_payment_date=date.today(),
            payment_frequency="monthly",
            payment_method="bank_transfer",
            status="active",
        )
        subscription_repository.save(new_sub)
        mock_session.add.assert_called_once_with(new_sub)
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once_with(new_sub)

    def test_delete_subscription(
        self,
        subscription_repository,
        mock_session,
        sample_subscriptions,
    ):
        subscription_repository.delete(sample_subscriptions[0])
        mock_session.delete.assert_called_once_with(sample_subscriptions[0])
        mock_session.commit.assert_called_once()

    def test_find_all_by_user_id_with_status_filter(
        self,
        subscription_repository,
        mock_session,
        sample_subscriptions,
        sample_user,
    ):
        mock_query = mock_session.query.return_value
        mock_query.filter.return_value.filter.return_value.order_by.return_value.limit.return_value.offset.return_value.all.return_value = [
            sample_subscriptions[0],
            sample_subscriptions[1],
            sample_subscriptions[2],
        ]
        filters = {"status": ["active"]}
        subscriptions = subscription_repository.find_all_by_user_id(
            sample_user.user_id,
            filters,
            "created_at",
            "asc",
            10,
            0,
        )
        assert len(subscriptions) == 3
        assert all(sub.status == "active" for sub in subscriptions)

    def test_find_all_by_user_id_with_currency_filter(
        self,
        subscription_repository,
        mock_session,
        sample_subscriptions,
        sample_user,
    ):
        mock_query = mock_session.query.return_value
        mock_query.filter.return_value.filter.return_value.order_by.return_value.limit.return_value.offset.return_value.all.return_value = [
            sample_subscriptions[0],
            sample_subscriptions[1],
        ]
        filters = {"currency": "USD"}
        subscriptions = subscription_repository.find_all_by_user_id(
            sample_user.user_id,
            filters,
            "created_at",
            "asc",
            10,
            0,
        )
        assert len(subscriptions) == 2
        assert all(sub.currency == "USD" for sub in subscriptions)

    def test_find_all_by_user_id_with_label_filter(
        self,
        subscription_repository,
        mock_session,
        sample_subscriptions,
        sample_user,
    ):
        # Mock the join operation
        mock_query = mock_session.query.return_value
        mock_query.filter.return_value.join.return_value.filter.return_value.order_by.return_value.limit.return_value.offset.return_value.all.return_value = [
            sample_subscriptions[0],
        ]

        filters = {"label_ids": [1]}
        subscriptions = subscription_repository.find_all_by_user_id(
            sample_user.user_id,
            filters,
            "created_at",
            "asc",
            10,
            0,
        )
        assert len(subscriptions) == 1
        mock_query.join.assert_called_once_with(Subscription.labels)
        # The mock fixture chains filter calls, so we check the count on the main filter mock
        assert mock_query.filter.call_count == 2

        # Check the label_id filter specifically
        last_filter_call = mock_query.filter.call_args
        label_filter_expr = last_filter_call[0][0]
        assert str(label_filter_expr) == str(Label.label_id.in_(filters["label_ids"]))

    def test_find_all_by_user_id_sort_by_name_desc(
        self,
        subscription_repository,
        mock_session,
        sample_subscriptions,
        sample_user,
    ):
        # Arrange: Mock the query to return subscriptions sorted by name descending
        mock_query = mock_session.query.return_value
        mock_query.filter.return_value.order_by.return_value.limit.return_value.offset.return_value.all.return_value = [
            sample_subscriptions[1],  # Spotify
            sample_subscriptions[0],  # Netflix
            sample_subscriptions[3],  # Paused Service
            sample_subscriptions[2],  # Hulu
        ]
        # Act
        subscriptions = subscription_repository.find_all_by_user_id(
            sample_user.user_id,
            {},
            "name",
            "desc",
            10,
            0,
        )
        # Assert
        assert subscriptions[0].name == "Spotify"
        assert subscriptions[1].name == "Netflix"
        assert subscriptions[2].name == "Paused Service"
        assert subscriptions[3].name == "Hulu"

        mock_query.filter.assert_called_once()
        filter_arg = mock_query.filter.call_args[0][0]
        assert str(filter_arg) == str(Subscription.user_id == sample_user.user_id)

        mock_query.order_by.assert_called_once()
        order_by_arg = mock_query.order_by.call_args[0][0]
        assert order_by_arg.element.name == "name"
        assert order_by_arg.modifier.__name__ == "desc_op"

    def test_find_all_by_user_id_sort_by_price_asc(
        self,
        subscription_repository,
        mock_session,
        sample_subscriptions,
        sample_user,
    ):
        # Arrange: Mock the query to return subscriptions sorted by price ascending
        mock_query = mock_session.query.return_value
        mock_query.filter.return_value.order_by.return_value.limit.return_value.offset.return_value.all.return_value = [
            sample_subscriptions[1],  # Spotify (5.0)
            sample_subscriptions[3],  # Paused Service (8.0)
            sample_subscriptions[0],  # Netflix (10.0)
            sample_subscriptions[2],  # Hulu (12.0)
        ]
        # Act
        subscriptions = subscription_repository.find_all_by_user_id(
            sample_user.user_id,
            {},
            "price",
            "asc",
            10,
            0,
        )
        # Assert
        assert subscriptions[0].price == 5.0
        assert subscriptions[1].price == 8.0
        assert subscriptions[2].price == 10.0
        assert subscriptions[3].price == 12.0

        mock_query = mock_session.query.return_value
        mock_query.filter.assert_called_once()
        filter_arg = mock_query.filter.call_args[0][0]
        assert str(filter_arg) == str(Subscription.user_id == sample_user.user_id)

        mock_query.order_by.assert_called_once()
        order_by_arg = mock_query.order_by.call_args[0][0]
        assert order_by_arg.element.name == "price"
        assert order_by_arg.modifier.__name__ == "asc_op"

    def test_find_all_by_user_id_pagination(
        self,
        subscription_repository,
        mock_session,
        sample_subscriptions,
        sample_user,
    ):
        mock_query = mock_session.query.return_value
        mock_query.filter.return_value.order_by.return_value.limit.return_value.offset.return_value.all.return_value = [
            sample_subscriptions[0],
        ]
        subscriptions = subscription_repository.find_all_by_user_id(
            sample_user.user_id,
            {},
            "created_at",
            "asc",
            1,
            0,
        )
        assert len(subscriptions) == 1
        assert subscriptions[0].subscription_id == 1
        mock_query.filter.return_value.order_by.return_value.limit.assert_called_once_with(
            1,
        )
        mock_query.filter.return_value.order_by.return_value.limit.return_value.offset.assert_called_once_with(
            0,
        )

    def test_find_all_by_user_id_no_sort_by_uses_default(
        self,
        subscription_repository,
        mock_session,
        sample_subscriptions,
        sample_user,
    ):
        mock_session.query.return_value.filter.return_value.order_by.return_value.limit.return_value.offset.return_value.all.return_value = [
            sample_subscriptions[0],
        ]
        subscription_repository.find_all_by_user_id(
            sample_user.user_id,
            {},
            None,
            "asc",
            1,
            0,
        )
        # Assert that order_by was called with the default 'created_at'
        mock_query = mock_session.query.return_value
        mock_query.order_by.assert_called_once()
        order_by_arg = mock_query.order_by.call_args[0][0]
        assert order_by_arg.element.name == "created_at"
        assert order_by_arg.modifier.__name__ == "asc_op"

    def test_find_all_by_user_id_invalid_sort_by_uses_default(
        self,
        subscription_repository,
        mock_session,
        sample_subscriptions,
        sample_user,
    ):
        mock_session.query.return_value.filter.return_value.order_by.return_value.limit.return_value.offset.return_value.all.return_value = [
            sample_subscriptions[0],
        ]
        subscription_repository.find_all_by_user_id(
            sample_user.user_id,
            {},
            "invalid_column",
            "asc",
            1,
            0,
        )
        # Assert that order_by was called with the default 'created_at'
        mock_query = mock_session.query.return_value
        mock_query.order_by.assert_called_once()
        order_by_arg = mock_query.order_by.call_args[0][0]
        assert order_by_arg.element.name == "created_at"
        assert order_by_arg.modifier.__name__ == "asc_op"

    def test_find_all_by_user_id_empty_filters(
        self,
        subscription_repository,
        mock_session,
        sample_subscriptions,
        sample_user,
    ):
        mock_query = mock_session.query.return_value
        mock_query.filter.return_value.order_by.return_value.limit.return_value.offset.return_value.all.return_value = (
            sample_subscriptions
        )
        subscriptions = subscription_repository.find_all_by_user_id(
            sample_user.user_id,
            {},
            "created_at",
            "asc",
            10,
            0,
        )
        assert len(subscriptions) == 4
        mock_query.filter.assert_called_once()
        filter_arg = mock_query.filter.call_args[0][0]
        assert str(filter_arg) == str(Subscription.user_id == sample_user.user_id)

    def test_find_due_subscriptions_with_next_payment_date_past(
        self,
        subscription_repository,
        mock_session,
        sample_subscriptions,
    ):
        today = date.today()
        # Subscription 1: next_payment_date = today
        # Subscription 3: next_payment_date = today - 5 days
        mock_session.query.return_value.filter.return_value.all.return_value = [
            sample_subscriptions[0],
            sample_subscriptions[2],
        ]
        due_subscriptions = subscription_repository.find_due_subscriptions(today)
        assert len(due_subscriptions) == 2
        assert due_subscriptions[0].subscription_id == 1
        assert due_subscriptions[1].subscription_id == 3

        mock_query = mock_session.query.return_value
        mock_query.filter.assert_called_once()

    def test_find_due_subscriptions_with_next_payment_date_future(
        self,
        subscription_repository,
        mock_session,
        sample_subscriptions,
    ):
        today = date.today()
        mock_session.query.return_value.filter.return_value.all.return_value = []
        due_subscriptions = subscription_repository.find_due_subscriptions(
            today - timedelta(days=10)
        )
        assert len(due_subscriptions) == 0

    def test_find_due_subscriptions_with_null_next_payment_date_and_initial_past(
        self,
        subscription_repository,
        mock_session,
        sample_user,
    ):
        today = date.today()
        # Create a subscription with next_payment_date = None and initial_payment_date in past
        sub_null_next_past_initial = Subscription(
            subscription_id=5,
            user_id=sample_user.user_id,
            name="New Service",
            price=10.0,
            currency="USD",
            initial_payment_date=today - timedelta(days=5),
            next_payment_date=None,
            payment_frequency="monthly",
            payment_method="credit_card",
            status="active",
        )
        mock_session.query.return_value.filter.return_value.all.return_value = [
            sub_null_next_past_initial,
        ]
        due_subscriptions = subscription_repository.find_due_subscriptions(today)
        assert len(due_subscriptions) == 1
        assert due_subscriptions[0].subscription_id == 5

    def test_find_due_subscriptions_with_null_next_payment_date_and_initial_future(
        self,
        subscription_repository,
        mock_session,
        sample_user,
    ):
        today = date.today()
        # Create a subscription with next_payment_date = None and initial_payment_date in future
        sub_null_next_future_initial = Subscription(
            subscription_id=6,
            user_id=sample_user.user_id,
            name="Future Service",
            price=10.0,
            currency="USD",
            initial_payment_date=today + timedelta(days=5),
            next_payment_date=None,
            payment_frequency="monthly",
            payment_method="credit_card",
            status="active",
        )
        mock_session.query.return_value.filter.return_value.all.return_value = []
        due_subscriptions = subscription_repository.find_due_subscriptions(today)
        assert len(due_subscriptions) == 0

    def test_find_due_subscriptions_ignores_paused_or_cancelled(
        self,
        subscription_repository,
        mock_session,
        sample_user,
    ):
        today = date.today()
        # Paused subscription (sample_subscriptions[3]) should be ignored
        mock_session.query.return_value.filter.return_value.all.return_value = []
        due_subscriptions = subscription_repository.find_due_subscriptions(today)
        assert len(due_subscriptions) == 0

    def test_update_next_payment_date(
        self,
        subscription_repository,
        mock_session,
        sample_subscriptions,
    ):
        subscription_to_update = sample_subscriptions[0]
        new_date = date.today() + timedelta(days=30)
        subscription_repository.update_next_payment_date(
            subscription_to_update, new_date
        )
        assert subscription_to_update.next_payment_date == new_date
        mock_session.add.assert_called_once_with(subscription_to_update)
        mock_session.commit.assert_called_once()
