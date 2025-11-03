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