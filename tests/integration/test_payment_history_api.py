"""
Payment History APIのエンドポイントに関する統合テスト。
"""

from collections.abc import Generator
from datetime import date, timedelta

import pytest
from flask.testing import FlaskClient
from sqlalchemy.orm import Session

from app.constants import ErrorMessages
from app.models.exchange_rate import ExchangeRate
from app.models.payment_history import PaymentHistory
from app.models.subscription import Subscription
from app.models.user import User
from tests.helpers import (
    assert_error_response,
    assert_success_response,
    make_and_save_subscription,
    make_and_save_user,
    make_api_headers,
)


@pytest.fixture
def authenticated_user(
    client: FlaskClient,
    clean_db: Generator[Session, None, None],
) -> dict:
    """認証済みのユーザーを作成し、APIヘッダーを返すフィクスチャ"""
    user = make_and_save_user(
        clean_db,
        username="payment_user",
        email="payment@example.com",
        password="password123",
    )
    headers = make_api_headers(user_id=user.user_id)
    return {"user": user, "headers": headers}


@pytest.fixture
def user_with_payment_histories(
    clean_db: Generator[Session, None, None],
    authenticated_user: dict,
) -> dict:
    """いくつかの支払履歴を持つ認証済みユーザーを準備する"""
    user: User = authenticated_user["user"]

    # サブスクリプションを作成
    sub1 = make_and_save_subscription(
        clean_db, user_id=user.user_id, name="Netflix", price=15.99
    )
    sub2 = make_and_save_subscription(
        clean_db, user_id=user.user_id, name="Spotify", price=9.99
    )

    # 為替レートを作成
    today = date.today()
    rate_date1 = today - timedelta(days=30)
    rate_date2 = today - timedelta(days=15)
    rate_date3 = today
    rates = [
        ExchangeRate(
            from_currency="USD",
            to_currency="JPY",
            date=rate_date1,
            rate=150.0,
            source="test",
        ),
        ExchangeRate(
            from_currency="USD",
            to_currency="JPY",
            date=rate_date2,
            rate=151.0,
            source="test",
        ),
        ExchangeRate(
            from_currency="USD",
            to_currency="JPY",
            date=rate_date3,
            rate=152.0,
            source="test",
        ),
    ]
    clean_db.add_all(rates)
    clean_db.commit()

    # 支払履歴を作成
    histories = [
        PaymentHistory(
            user_id=user.user_id,
            subscription_id=sub1.subscription_id,
            subscription_name=sub1.name,
            payment_date=rate_date1,
            amount=15.99,
            currency="USD",
            rate_from_currency="USD",
            rate_to_currency="JPY",
            rate_date=rate_date1,
            payment_method="credit_card",
        ),
        PaymentHistory(
            user_id=user.user_id,
            subscription_id=sub2.subscription_id,
            subscription_name=sub2.name,
            payment_date=rate_date2,
            amount=9.99,
            currency="USD",
            rate_from_currency="USD",
            rate_to_currency="JPY",
            rate_date=rate_date2,
            payment_method="credit_card",
        ),
        PaymentHistory(
            user_id=user.user_id,
            subscription_id=sub1.subscription_id,
            subscription_name=sub1.name,
            payment_date=rate_date3,
            amount=15.99,
            currency="USD",
            rate_from_currency="USD",
            rate_to_currency="JPY",
            rate_date=rate_date3,
            payment_method="paypal",
        ),
    ]
    clean_db.add_all(histories)
    clean_db.commit()

    # 他のユーザーの支払履歴(これは取得されてはいけない)
    other_user = make_and_save_user(
        clean_db, username="other_user", email="other@example.com"
    )
    other_sub = make_and_save_subscription(
        clean_db, user_id=other_user.user_id, name="Disney+", price=7.99
    )
    other_history = PaymentHistory(
        user_id=other_user.user_id,
        subscription_id=other_sub.subscription_id,
        subscription_name=other_sub.name,
        payment_date=today,
        amount=7.99,
        currency="USD",
        rate_from_currency="USD",
        rate_to_currency="JPY",
        rate_date=today,
        payment_method="credit_card",
    )
    clean_db.add(other_history)
    clean_db.commit()

    authenticated_user["subscriptions"] = [sub1, sub2]
    return authenticated_user


@pytest.mark.api
class TestGetPaymentHistoryAPI:
    """GET /api/v1/payments"""

    def test_get_payment_history_returns_list_for_owner(
        self, client: FlaskClient, user_with_payment_histories: dict
    ):
        """[正常系] 認証済みユーザーが自身の支払履歴一覧を正しく取得できる"""
        headers = user_with_payment_histories["headers"]

        response = client.get("/api/v1/payments", headers=headers)

        data = assert_success_response(response, 200)
        assert "payments" in data["data"]
        assert "meta" in data
        payments = data["data"]["payments"]
        meta = data["meta"]
        assert len(payments) == 3
        assert meta["total"] == 3
        assert payments[0]["subscription_name"] == "Netflix"  # Default sort is date desc

    def test_get_payment_history_unauthorized_without_token(self, client: FlaskClient):
        """[異常系] 認証トークンがない場合は401エラーを返す"""
        response = client.get("/api/v1/payments")
        assert_error_response(response, 401)

    def test_get_payment_history_returns_empty_list_for_no_history_user(
        self, client: FlaskClient, authenticated_user: dict
    ):
        """[正常系] 支払履歴がないユーザーには空のリストを返す"""
        headers = authenticated_user["headers"]
        response = client.get("/api/v1/payments", headers=headers)
        data = assert_success_response(response, 200)
        assert len(data["data"]["payments"]) == 0
        assert data["meta"]["total"] == 0

    def test_filter_by_subscription_id(
        self, client: FlaskClient, user_with_payment_histories: dict
    ):
        """[正常系] subscription_idで支払履歴をフィルタリングできる"""
        headers = user_with_payment_histories["headers"]
        sub1: Subscription = user_with_payment_histories["subscriptions"][0]

        response = client.get(
            f"/api/v1/payments?subscription_id={sub1.subscription_id}", headers=headers
        )

        data = assert_success_response(response, 200)
        assert len(data["data"]["payments"]) == 2
        assert data["meta"]["total"] == 2
        assert all(
            p["subscription_name"] == "Netflix" for p in data["data"]["payments"]
        )

    def test_filter_by_date_range(
        self, client: FlaskClient, user_with_payment_histories: dict
    ):
        """[正常系] 日付範囲で支払履歴をフィルタリングできる"""
        headers = user_with_payment_histories["headers"]
        start_date = date.today() - timedelta(days=20)
        end_date = date.today() - timedelta(days=10)

        response = client.get(
            f"/api/v1/payments?start_date={start_date}&end_date={end_date}",
            headers=headers,
        )

        data = assert_success_response(response, 200)
        assert len(data["data"]["payments"]) == 1
        assert data["meta"]["total"] == 1
        assert data["data"]["payments"][0]["subscription_name"] == "Spotify"

    def test_pagination(self, client: FlaskClient, user_with_payment_histories: dict):
        """[正常系] 支払履歴をページネーションで取得できる"""
        headers = user_with_payment_histories["headers"]

        response = client.get("/api/v1/payments?limit=1&offset=1", headers=headers)

        data = assert_success_response(response, 200)
        assert len(data["data"]["payments"]) == 1
        assert data["meta"]["total"] == 3
        # Sorted by date desc, so second item is Spotify
        assert data["data"]["payments"][0]["subscription_name"] == "Spotify"

    def test_sorting(self, client: FlaskClient, user_with_payment_histories: dict):
        """[正常系] 支払履歴をソートできる"""
        headers = user_with_payment_histories["headers"]

        response = client.get(
            "/api/v1/payments?sort_by=amount&sort_order=asc", headers=headers
        )

        data = assert_success_response(response, 200)
        assert len(data["data"]["payments"]) == 3
        assert data["data"]["payments"][0]["amount"] == 9.99  # Spotify
        assert data["data"]["payments"][1]["amount"] == 15.99 # Netflix
        assert data["data"]["payments"][2]["amount"] == 15.99 # Netflix

    def test_invalid_filter_param_returns_400(
        self, client: FlaskClient, authenticated_user: dict
    ):
        """[異常系] 不正なフィルタパラメータは400エラーを返す"""
        headers = authenticated_user["headers"]
        response = client.get("/api/v1/payments?sort_by=invalid_column", headers=headers)
        assert_error_response(response, 400)


@pytest.fixture
def user_with_subscription(
    clean_db: Generator[Session, None, None],
    authenticated_user: dict,
) -> dict:
    """サブスクリプションを持つ認証済みユーザーを準備する"""
    user: User = authenticated_user["user"]

    subscription = make_and_save_subscription(
        clean_db,
        user_id=user.user_id,
        name="Netflix",
        price=15.99,
        currency="USD",  # Assume USD as base currency for this user
    )
    authenticated_user["subscription"] = subscription
    return authenticated_user


@pytest.fixture
def user_with_subscription_and_rate(
    clean_db: Generator[Session, None, None],
    authenticated_user: dict,
) -> dict:
    """サブスクリプションと為替レートを持つ認証済みユーザーを準備する"""
    user: User = authenticated_user["user"]
    user.base_currency = "USD"
    clean_db.add(user)
    clean_db.commit()

    subscription = make_and_save_subscription(
        clean_db,
        user_id=user.user_id,
        name="Foreign Sub",
        price=1500,
        currency="JPY",
    )

    rate = ExchangeRate(
        from_currency="JPY",
        to_currency="USD",
        date=date(2025, 1, 15),
        rate=150.0,
        source="test",
    )
    clean_db.add(rate)
    clean_db.commit()

    authenticated_user["subscription"] = subscription
    authenticated_user["rate"] = rate
    return authenticated_user


@pytest.mark.api
class TestCreatePaymentHistoryAPI:
    """POST /api/v1/payments"""

    def test_create_payment_with_base_currency_returns_201(
        self,
        client: FlaskClient,
        user_with_subscription: dict,
    ):
        """
        [正常系] POST /payments:

        基本通貨での支払い履歴登録が成功し、201 Created を返すことを期待するテスト。
        """
        # Arrange
        headers = user_with_subscription["headers"]
        subscription: Subscription = user_with_subscription["subscription"]
        user: User = user_with_subscription["user"]

        payment_data = {
            "subscription_id": subscription.subscription_id,
            "payment_date": "2025-01-01",
            "amount": 10.00,
            "currency": user.base_currency,  # User's base currency, e.g., USD
            "payment_method": "credit_card",
        }

        # Act
        response = client.post(
            "/api/v1/payments",
            json=payment_data,
            headers=headers,
        )

        # Assert
        data = assert_success_response(response, 201)
        assert data["data"]["subscription_id"] == subscription.subscription_id
        assert data["data"]["amount"] == 10.00
        assert data["data"]["currency"] == user.base_currency
        assert data["data"]["converted_amount"] == 10.00 # For base currency, converted_amount should be same
        assert data["data"]["user_id"] == user.user_id

    def test_create_payment_with_foreign_currency_returns_201(
        self,
        client: FlaskClient,
        user_with_subscription_and_rate: dict,
    ):
        """
        [レッドフェーズ] POST /payments:

        外貨での支払い履歴登録が成功し、為替レートが適用されて 201 Created を返すことを期待するテスト。
        """
        # Arrange
        headers = user_with_subscription_and_rate["headers"]
        subscription: Subscription = user_with_subscription_and_rate["subscription"]
        user: User = user_with_subscription_and_rate["user"]
        rate: ExchangeRate = user_with_subscription_and_rate["rate"]

        payment_data = {
            "subscription_id": subscription.subscription_id,
            "payment_date": rate.date.isoformat(),
            "amount": 1500,
            "currency": "JPY", # Foreign currency
            "payment_method": "credit_card",
        }

        # Act
        response = client.post(
            "/api/v1/payments",
            json=payment_data,
            headers=headers,
        )

        # Assert
        data = assert_success_response(response, 201)
        assert data["data"]["currency"] == "JPY"
        assert data["data"]["exchange_rate"] == rate.rate
        assert data["data"]["converted_amount"] == 1500 / rate.rate # 1500 / 150 = 10
        assert data["data"]["rate_from_currency"] == "JPY"
        assert data["data"]["rate_to_currency"] == "USD"

    def test_create_payment_with_missing_required_field_returns_400(
        self,
        client: FlaskClient,
        user_with_subscription: dict,
    ):
        """
        [レッドフェーズ] POST /payments:

        必須項目（amount）が欠けている場合に400 Bad Requestを返すことを期待するテスト。
        """
        # Arrange
        headers = user_with_subscription["headers"]
        subscription: Subscription = user_with_subscription["subscription"]
        user: User = user_with_subscription["user"]

        # amount is missing
        payment_data = {
            "subscription_id": subscription.subscription_id,
            "payment_date": "2025-01-01",
            "currency": user.base_currency,
            "payment_method": "credit_card",
        }

        # Act
        response = client.post(
            "/api/v1/payments",
            json=payment_data,
            headers=headers,
        )

        # Assert
        assert_error_response(response, 400)

    def test_create_payment_for_non_existent_subscription_returns_404(
        self,
        client: FlaskClient,
        authenticated_user: dict,
    ):
        """
        [レッドフェーズ] POST /payments:

        存在しないsubscription_idを指定した場合に404 Not Foundを返すことを期待するテスト。
        """
        # Arrange
        headers = authenticated_user["headers"]
        payment_data = {
            "subscription_id": 9999,  # Non-existent
            "payment_date": "2025-01-01",
            "amount": 10.00,
            "currency": "USD",
            "payment_method": "credit_card",
        }

        # Act
        response = client.post(
            "/api/v1/payments",
            json=payment_data,
            headers=headers,
        )

        # Assert
        assert_error_response(response, 404)

    def test_create_payment_for_other_users_subscription_returns_403(
        self,
        client: FlaskClient,
        user_with_subscription: dict, # This user is the attacker
        clean_db: Session,
    ):
        """
        [レッドフェーズ] POST /payments:

        他のユーザーのsubscription_idを指定した場合に403 Forbiddenを返すことを期待するテスト。
        """
        # Arrange
        # Create another user and their subscription (the victim)
        victim_user = make_and_save_user(clean_db, username="victim", email="victim@example.com")
        victim_subscription = make_and_save_subscription(clean_db, user_id=victim_user.user_id, name="Victim Sub")
        
        attacker_headers = user_with_subscription["headers"]
        
        payment_data = {
            "subscription_id": victim_subscription.subscription_id,
            "payment_date": "2025-01-01",
            "amount": 10.00,
            "currency": "USD",
            "payment_method": "credit_card",
        }

        # Act
        response = client.post(
            "/api/v1/payments",
            json=payment_data,
            headers=attacker_headers,
        )

        # Assert
        assert_error_response(response, 403)

    def test_create_payment_with_missing_exchange_rate_returns_400(
        self,
        client: FlaskClient,
        user_with_subscription: dict, # Using this fixture as it doesn't create a rate for JPY->USD
    ):
        """
        [レッドフェーズ] POST /payments:

        為替レートが見つからない場合に400 Bad Requestを返すことを期待するテスト。
        """
        # Arrange
        headers = user_with_subscription["headers"]
        subscription: Subscription = user_with_subscription["subscription"]
        user: User = user_with_subscription["user"]

        # Ensure a different base currency for the user for this test
        user.base_currency = "USD"
        # make_and_save_user is not ideal here, but to reuse user_with_subscription,
        # we directly change the user's base_currency.
        # This test relies on there being NO JPY->USD rate for this date.
        
        payment_data = {
            "subscription_id": subscription.subscription_id,
            "payment_date": "2025-01-01", # Date where no JPY-USD rate exists in current fixtures
            "amount": 1000.00,
            "currency": "JPY", # Different from user's base_currency (USD)
            "payment_method": "credit_card",
        }

        # Act
        response = client.post(
            "/api/v1/payments",
            json=payment_data,
            headers=headers,
        )

        # Assert
        assert_error_response(response, 400)


        

        
