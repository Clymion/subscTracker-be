"""
Subscription APIのエンドポイントに関する統合テスト。

TDD（テスト駆動開発）のアプローチに従い、APIの振る舞いを定義します。
"""

from collections.abc import Generator

import pytest
from flask.testing import FlaskClient
from sqlalchemy.orm import Session

from app.constants import ErrorMessages
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
        username="subsc_user",
        email="subsc@example.com",
        password="password123",
    )
    headers = make_api_headers(user_id=user.user_id)
    return {"user": user, "headers": headers}


@pytest.fixture
def user_with_subscriptions(
    clean_db: Generator[Session, None, None],
    authenticated_user: dict,
) -> dict:
    """いくつかのサブスクリプションを持つ認証済みユーザーを準備する"""
    user: User = authenticated_user["user"]

    # 自分のサブスクリプション
    make_and_save_subscription(
        clean_db,
        user_id=user.user_id,
        name="Netflix",
        price=15.99,
    )
    make_and_save_subscription(
        clean_db,
        user_id=user.user_id,
        name="Spotify",
        price=9.99,
    )

    # 別のユーザーのサブスクリプション(これは取得されてはいけない)  # noqa: ERA001
    other_user = make_and_save_user(
        clean_db,
        username="other_user",
        email="other@example.com",
    )
    make_and_save_subscription(
        clean_db,
        user_id=other_user.user_id,
        name="Disney+",
        price=7.99,
    )

    return authenticated_user


@pytest.mark.api
class TestGetSubscriptionsAPI:
    """GET /api/v1/subscriptions"""

    def test_get_subscriptions_returns_list_for_owner(
        self,
        client: FlaskClient,
        user_with_subscriptions: dict,
    ):
        """
        [正常系] GET /subscriptions:

        認証済みユーザーが自身のサブスクリプション一覧を正しく取得できる
        """
        # Arrange
        headers = user_with_subscriptions["headers"]

        # Act
        response = client.get("/api/v1/subscriptions", headers=headers)

        # Assert
        data = assert_success_response(response, 200)
        assert "subscriptions" in data["data"]
        subscriptions = data["data"]["subscriptions"]
        assert len(subscriptions) == 2
        subscription_names = {sub["name"] for sub in subscriptions}
        assert subscription_names == {"Netflix", "Spotify"}
        # レスポンスが完全なオブジェクトであることを確認
        assert "initial_payment_date" in subscriptions[0]
        assert "notes" in subscriptions[0]

    def test_get_subscriptions_returns_empty_list_for_user_with_no_subs(
        self,
        client: FlaskClient,
        authenticated_user: dict,
    ):
        """
        [正常系] GET /subscriptions: サブスクリプションを一つも持たないユーザーには空のリストを返す
        """
        # Arrange
        headers = authenticated_user["headers"]

        # Act
        response = client.get("/api/v1/subscriptions", headers=headers)

        # Assert
        data = assert_success_response(response, 200)
        assert "subscriptions" in data["data"]
        assert len(data["data"]["subscriptions"]) == 0

    def test_get_subscriptions_unauthorized_without_token(self, client: FlaskClient):
        """
        [異常系] GET /subscriptions: 認証トークンがない場合は401エラーを返す
        """
        # Act
        response = client.get("/api/v1/subscriptions")

        # Assert
        assert_error_response(response, 401)


@pytest.mark.api
class TestCreateSubscriptionAPI:
    """POST /api/v1/subscriptions"""

    def test_create_subscription_with_valid_data_returns_201(
        self,
        client: FlaskClient,
        authenticated_user: dict,
    ):
        """
        [正常系] POST /subscriptions:

        有効なデータでサブスクリプションを新規作成できることをテストする
        """
        # Arrange
        headers = authenticated_user["headers"]
        subscription_data = {
            "name": "Youtube Premium",
            "price": 11.99,
            "currency": "USD",
            "initial_payment_date": "2024-05-01",
            "payment_frequency": "monthly",
            "payment_method": "credit_card",
            "status": "active",
            "notes": "Family plan",
        }

        # Act
        response = client.post(
            "/api/v1/subscriptions",
            json=subscription_data,
            headers=headers,
        )

        # Assert
        data = assert_success_response(response, 201)
        created_sub = data["data"]
        assert created_sub["name"] == "Youtube Premium"
        assert created_sub["price"] == 11.99
        assert created_sub["status"] == "active"
        assert created_sub["notes"] == "Family plan"
        # 次回支払日が正しく計算されているか
        assert "next_payment_date" in created_sub
        assert created_sub["next_payment_date"] > created_sub["initial_payment_date"]

    def test_create_subscription_with_duplicate_name_returns_400(
        self,
        client: FlaskClient,
        user_with_subscriptions: dict,
    ):
        """
        [異常系] POST /subscriptions:

        同じユーザーに対して重複した名前のサブスクリプションは作成できない
        """
        # Arrange
        headers = user_with_subscriptions["headers"]
        # 既存のサブスクリプション名 "Netflix" を使用
        subscription_data = {
            "name": "Netflix",
            "price": 9.99,
            "currency": "USD",
            "initial_payment_date": "2024-06-01",
            "payment_frequency": "monthly",
            "payment_method": "credit_card",
            "status": "active",
        }

        # Act
        response = client.post(
            "/api/v1/subscriptions",
            json=subscription_data,
            headers=headers,
        )

        # Assert
        assert_error_response(response, 400, ErrorMessages.DUPLICATE_SUBSCRIPTION)

    def test_create_subscription_with_invalid_price_returns_400(
        self,
        client: FlaskClient,
        authenticated_user: dict,
    ):
        """
        [異常系] POST /subscriptions: 価格が0以下の場合は400エラーを返す
        """
        # Arrange
        headers = authenticated_user["headers"]
        subscription_data = {
            "name": "Invalid Price Sub",
            "price": -5.00,  # 無効な価格
            "currency": "USD",
            "initial_payment_date": "2024-06-01",
            "payment_frequency": "monthly",
            "payment_method": "credit_card",
            "status": "active",
        }

        # Act
        response = client.post(
            "/api/v1/subscriptions",
            json=subscription_data,
            headers=headers,
        )

        # Assert
        assert_error_response(response, 400)

    def test_create_subscription_with_missing_required_field_returns_400(
        self,
        client: FlaskClient,
        authenticated_user: dict,
    ):
        """
        [異常系] POST /subscriptions: 必須フィールドが欠けている場合は400エラーを返す
        """
        # Arrange
        headers = authenticated_user["headers"]
        # "price" フィールドが欠けている
        subscription_data = {
            "name": "Missing Field Sub",
            "currency": "USD",
            "initial_payment_date": "2024-06-01",
            "payment_frequency": "monthly",
            "payment_method": "credit_card",
            "status": "active",
        }

        # Act
        response = client.post(
            "/api/v1/subscriptions",
            json=subscription_data,
            headers=headers,
        )

        # Assert
        assert_error_response(response, 400)


@pytest.mark.api
class TestGetSubscriptionDetailAPI:
    """GET /api/v1/subscriptions/{id}"""

    def test_get_subscription_by_id_returns_details_for_owner(
        self,
        client: FlaskClient,
        user_with_subscriptions: dict,
    ):
        """
        [正常系] GET /subscriptions/{id}: 自分のサブスクリプションIDを指定して、詳細を取得
        """
        # Arrange
        headers = user_with_subscriptions["headers"]
        user = user_with_subscriptions["user"]
        # ユーザーが所有するサブスクリプションを1つ取得
        sub_id = user.subscriptions[0].subscription_id

        # Act
        response = client.get(f"/api/v1/subscriptions/{sub_id}", headers=headers)

        # Assert
        data = assert_success_response(response, 200)
        retrieved_sub = data["data"]
        assert retrieved_sub["subscription_id"] == sub_id
        assert retrieved_sub["name"] == user.subscriptions[0].name

    def test_get_subscription_by_id_returns_404_for_non_existent_id(
        self,
        client: FlaskClient,
        authenticated_user: dict,
    ):
        """
        [異常系] GET /subscriptions/{id}: 存在しないIDを指定した場合、404エラーが返ってくる
        """
        # Arrange
        headers = authenticated_user["headers"]
        non_existent_id = 9999

        # Act
        response = client.get(
            f"/api/v1/subscriptions/{non_existent_id}",
            headers=headers,
        )

        # Assert
        assert_error_response(response, 404, ErrorMessages.SUBSCRIPTION_NOT_FOUND)

    def test_get_subscription_by_id_returns_404_for_other_users_sub(
        self,
        client: FlaskClient,
        user_with_subscriptions: dict,
    ):
        """
        [異常系] GET /subscriptions/{id}:

        他のユーザーのサブスクリプションIDを指定した場合、404エラーが返ってくる
        """
        # Arrange
        headers = user_with_subscriptions["headers"]
        # 他のユーザーのサブスクリプションIDを取得
        other_user = User.query.filter(User.username == "other_user").one()
        other_sub_id = other_user.subscriptions[0].subscription_id

        # Act
        response = client.get(f"/api/v1/subscriptions/{other_sub_id}", headers=headers)

        # Assert
        assert_error_response(response, 404, ErrorMessages.SUBSCRIPTION_NOT_FOUND)


@pytest.mark.api
class TestUpdateSubscriptionAPI:
    """PUT /api/v1/subscriptions/{id}"""

    def test_update_subscription_with_valid_data_returns_200(
        self,
        client: FlaskClient,
        user_with_subscriptions: dict,
    ):
        """
        [正常系] PUT /subscriptions/{id}: 有効なデータでサブスクリプションを更新
        """
        # Arrange
        headers = user_with_subscriptions["headers"]
        user = user_with_subscriptions["user"]
        sub_to_update = user.subscriptions[0]
        update_data = {
            "name": "Netflix Family Plan",
            "price": 20.50,
            "status": "suspended",
        }

        # Act
        response = client.put(
            f"/api/v1/subscriptions/{sub_to_update.subscription_id}",
            json=update_data,
            headers=headers,
        )

        # Assert
        data = assert_success_response(response, 200)
        updated_sub = data["data"]
        assert updated_sub["name"] == "Netflix Family Plan"
        assert updated_sub["price"] == 20.50
        assert updated_sub["status"] == "suspended"

    def test_update_subscription_returns_404_for_other_users_sub(
        self,
        client: FlaskClient,
        user_with_subscriptions: dict,
    ):
        """
        [異常系] PUT /subscriptions/{id}: 他のユーザーのサブスクリプションは更新できない
        """
        # Arrange
        headers = user_with_subscriptions["headers"]
        other_user = User.query.filter(User.username == "other_user").one()
        other_sub_id = other_user.subscriptions[0].subscription_id
        update_data = {"name": "Hacked!"}

        # Act
        response = client.put(
            f"/api/v1/subscriptions/{other_sub_id}",
            json=update_data,
            headers=headers,
        )

        # Assert
        assert_error_response(response, 404, ErrorMessages.SUBSCRIPTION_NOT_FOUND)


@pytest.mark.api
class TestDeleteSubscriptionAPI:
    """DELETE /api/v1/subscriptions/{id}"""

    def test_delete_subscription_returns_204_and_removes_record(
        self,
        client: FlaskClient,
        user_with_subscriptions: dict,
        clean_db: Session,
    ):
        """
        [正常系] DELETE /subscriptions/{id}: サブスクリプションを正常に削除
        """
        # Arrange
        headers = user_with_subscriptions["headers"]
        user = user_with_subscriptions["user"]
        sub_to_delete = user.subscriptions[0]
        sub_id = sub_to_delete.subscription_id

        # Act
        response = client.delete(
            f"/api/v1/subscriptions/{sub_id}",
            headers=headers,
        )

        # Assert
        assert response.status_code == 204

        # 再度GETして、404が返ってくることを確認
        get_response = client.get(f"/api/v1/subscriptions/{sub_id}", headers=headers)
        assert_error_response(get_response, 404)

    def test_delete_subscription_returns_404_for_non_existent_id(
        self,
        client: FlaskClient,
        authenticated_user: dict,
    ):
        """
        [異常系] DELETE /subscriptions/{id}: 存在しないIDを削除しようとすると404エラーになる
        """
        # Arrange
        headers = authenticated_user["headers"]
        non_existent_id = 9999

        # Act
        response = client.delete(
            f"/api/v1/subscriptions/{non_existent_id}",
            headers=headers,
        )

        # Assert
        assert_error_response(response, 404, ErrorMessages.SUBSCRIPTION_NOT_FOUND)

    def test_delete_subscription_returns_404_for_other_users_sub(
        self,
        client: FlaskClient,
        user_with_subscriptions: dict,
    ):
        """
        [異常系] DELETE /subscriptions/{id}: 他のユーザーのサブスクリプションは削除できない
        """
        # Arrange
        headers = user_with_subscriptions["headers"]
        other_user = User.query.filter(User.username == "other_user").one()
        other_sub_id = other_user.subscriptions[0].subscription_id

        # Act
        response = client.delete(
            f"/api/v1/subscriptions/{other_sub_id}",
            headers=headers,
        )

        # Assert
        assert_error_response(response, 404, ErrorMessages.SUBSCRIPTION_NOT_FOUND)
