"""
ユーザープロフィールAPIの統合テスト

GET /api/v1/users/{userId} エンドポイントのテスト
"""

from collections.abc import Generator

import pytest
from flask.testing import FlaskClient
from sqlalchemy.orm import Session

from app.models.user import User
from tests.helpers import (
    assert_error_response,
    assert_success_response,
    make_access_token,
    make_and_save_label,
    make_and_save_subscription,
    make_and_save_user,
    make_api_headers,
)


@pytest.fixture
def authenticated_user(
    client: FlaskClient,
    clean_db: Generator[Session, None, None],
) -> dict:
    """
    認証済みユーザーを作成し、アクセストークンを返す

    Args:
        client: Flaskテストクライアント
        clean_db: クリーンなデータベースセッション

    Returns:
        dict: ユーザー情報と認証ヘッダーを含む辞書
    """
    user = make_and_save_user(
        clean_db,
        username="testuser",
        email="test@example.com",
        password="testpassword123",
    )

    access_token = make_access_token(user.user_id)
    headers = make_api_headers()
    headers["Authorization"] = f"Bearer {access_token}"

    return {
        "user": user,
        "access_token": access_token,
        "headers": headers,
    }


@pytest.mark.api
@pytest.mark.auth
class TestGetUserProfile:
    """GET /api/v1/users/{userId} エンドポイントのテスト"""

    def test_get_profile_authenticated_user(
        self,
        client: FlaskClient,
        authenticated_user: dict,
    ):
        """
        タスク1.1: 認証済みユーザーが自分のプロフィールを取得できることを検証する

        有効なJWTトークンでGET /api/v1/users/{userId}を呼び出す
        レスポンスがユーザーID、ユーザー名、メールアドレス、基準通貨、作成日時を含むことを確認
        レスポンス形式が`data`フィールドを持つことを確認

        Requirements: 1.1, 4.1
        """
        # Arrange
        user = authenticated_user["user"]
        headers = authenticated_user["headers"]

        # Act
        response = client.get(f"/api/v1/users/{user.user_id}", headers=headers)

        # Assert
        data = assert_success_response(response, expected_status=200)
        assert "data" in data

        profile = data["data"]
        assert profile["id"] == str(user.user_id)
        assert profile["username"] == user.username
        assert profile["email"] == user.email
        assert profile["base_currency"] == user.base_currency
        assert "created_at" in profile

    def test_get_profile_unauthenticated_user(
        self,
        client: FlaskClient,
        clean_db: Generator[Session, None, None],
    ):
        """
        タスク1.2: 未認証ユーザーが401エラーを受け取ることを検証する

        JWTトークンなしでGET /api/v1/users/{userId}を呼び出す
        レスポンスが401ステータスコードであることを確認
        エラーレスポンスが`error`フィールドを持つことを確認

        Requirements: 1.2, 4.2
        """
        # Arrange
        user = make_and_save_user(clean_db)
        headers = {"Content-Type": "application/json"}  # Authorization headerなし

        # Act
        response = client.get(f"/api/v1/users/{user.user_id}", headers=headers)

        # Assert
        assert_error_response(response, expected_status=401)

    def test_get_profile_other_user_forbidden(
        self,
        client: FlaskClient,
        clean_db: Generator[Session, None, None],
    ):
        """
        タスク1.3: 他のユーザーのプロフィール取得で403エラーになることを検証する

        ユーザーAのトークンでユーザーBのプロフィールを取得しようとする
        レスポンスが403ステータスコードであることを確認

        Requirements: 1.3
        """
        # Arrange
        user_a = make_and_save_user(
            clean_db,
            username="userA",
            email="userA@example.com",
            password="password123",
        )
        user_b = make_and_save_user(
            clean_db,
            username="userB",
            email="userB@example.com",
            password="password123",
        )

        # ユーザーAのトークンを作成
        access_token = make_access_token(user_a.user_id)
        headers = {"Content-Type": "application/json"}
        headers["Authorization"] = f"Bearer {access_token}"

        # Act: ユーザーAのトークンでユーザーBのプロフィールを取得
        response = client.get(f"/api/v1/users/{user_b.user_id}", headers=headers)

        # Assert
        assert_error_response(response, expected_status=403)

    def test_get_profile_nonexistent_user(
        self,
        client: FlaskClient,
        authenticated_user: dict,
    ):
        """
        タスク1.4: 存在しないユーザーIDで404エラーになることを検証する

        存在しないユーザーIDでGET /api/v1/users/{userId}を呼び出す
        レスポンスが404ステータスコードであることを確認

        Requirements: 1.4
        """
        # Arrange
        headers = authenticated_user["headers"]
        nonexistent_user_id = 99999

        # Act
        response = client.get(f"/api/v1/users/{nonexistent_user_id}", headers=headers)

        # Assert
        assert_error_response(response, expected_status=404)


@pytest.mark.api
@pytest.mark.auth
class TestUpdateUserProfile:
    """PATCH /api/v1/users/{userId} エンドポイントのテスト"""

    def test_update_username_success(
        self,
        client: FlaskClient,
        authenticated_user: dict,
    ):
        """
        タスク2.1: ユーザー名の更新を検証する

        有効なユーザー名（3-32文字）でPATCH /api/v1/users/{userId}を呼び出す
        更新後のユーザー名がレスポンスに反映されることを確認

        Requirements: 2.1, 2.2
        """
        # Arrange
        user = authenticated_user["user"]
        headers = authenticated_user["headers"]
        new_username = "updateduser"

        # Act
        response = client.patch(
            f"/api/v1/users/{user.user_id}",
            headers=headers,
            json={"username": new_username},
        )

        # Assert
        data = assert_success_response(response, expected_status=200)
        assert "data" in data
        profile = data["data"]
        assert profile["username"] == new_username
        assert profile["email"] == user.email
        assert profile["base_currency"] == user.base_currency

    def test_update_email_success(
        self,
        client: FlaskClient,
        authenticated_user: dict,
    ):
        """
        タスク2.2: メールアドレスの更新を検証する

        有効なメールフォーマットでPATCH /api/v1/users/{userId}を呼び出す
        更新後のメールアドレスがレスポンスに反映されることを確認

        Requirements: 2.1, 2.3
        """
        # Arrange
        user = authenticated_user["user"]
        headers = authenticated_user["headers"]
        new_email = "updated@example.com"

        # Act
        response = client.patch(
            f"/api/v1/users/{user.user_id}",
            headers=headers,
            json={"email": new_email},
        )

        # Assert
        data = assert_success_response(response, expected_status=200)
        assert "data" in data
        profile = data["data"]
        assert profile["email"] == new_email
        assert profile["username"] == user.username
        assert profile["base_currency"] == user.base_currency

    def test_update_base_currency_success(
        self,
        client: FlaskClient,
        authenticated_user: dict,
    ):
        """
        タスク2.3: 基準通貨の更新を検証する

        有効な通貨コード（JPY, USD, EUR, GBP）で更新
        更新が正常に行われることを確認

        Requirements: 2.1, 2.4
        """
        # Arrange
        user = authenticated_user["user"]
        headers = authenticated_user["headers"]
        new_currency = "JPY"

        # Act
        response = client.patch(
            f"/api/v1/users/{user.user_id}",
            headers=headers,
            json={"base_currency": new_currency},
        )

        # Assert
        data = assert_success_response(response, expected_status=200)
        assert "data" in data
        profile = data["data"]
        assert profile["base_currency"] == new_currency
        assert profile["username"] == user.username
        assert profile["email"] == user.email

    def test_update_email_duplicate_error(
        self,
        client: FlaskClient,
        clean_db: Generator[Session, None, None],
    ):
        """
        タスク2.4: メール重複で400エラーになることを検証する

        既に使用されているメールアドレスに更新しようとする
        レスポンスが400ステータスコードであることを確認

        Requirements: 2.5
        """
        # Arrange
        user_a = make_and_save_user(
            clean_db,
            username="userA",
            email="userA@example.com",
            password="password123",
        )
        user_b = make_and_save_user(
            clean_db,
            username="userB",
            email="userB@example.com",
            password="password123",
        )

        access_token = make_access_token(user_a.user_id)
        headers = make_api_headers()
        headers["Authorization"] = f"Bearer {access_token}"

        # Act: user_aがuser_bのメールアドレスに更新しようとする
        response = client.patch(
            f"/api/v1/users/{user_a.user_id}",
            headers=headers,
            json={"email": user_b.email},
        )

        # Assert
        assert_error_response(response, expected_status=400)

    def test_update_invalid_currency_error(
        self,
        client: FlaskClient,
        authenticated_user: dict,
    ):
        """
        タスク2.5: 無効な通貨コードで400エラーになることを検証する

        無効な通貨コード（例: "XYZ"）で更新しようとする
        レスポンスが400ステータスコードであることを確認

        Requirements: 2.6
        """
        # Arrange
        user = authenticated_user["user"]
        headers = authenticated_user["headers"]
        invalid_currency = "XYZ"

        # Act
        response = client.patch(
            f"/api/v1/users/{user.user_id}",
            headers=headers,
            json={"base_currency": invalid_currency},
        )

        # Assert
        assert_error_response(response, expected_status=400)

    def test_update_unauthenticated_error(
        self,
        client: FlaskClient,
        clean_db: Generator[Session, None, None],
    ):
        """
        タスク2.6: 未認証ユーザーが更新で401エラーになることを検証する

        JWTトークンなしでPATCH /api/v1/users/{userId}を呼び出す
        レスポンスが401ステータスコードであることを確認

        Requirements: 2.7, 4.2
        """
        # Arrange
        user = make_and_save_user(clean_db)
        headers = {"Content-Type": "application/json"}  # Authorization headerなし

        # Act
        response = client.patch(
            f"/api/v1/users/{user.user_id}",
            headers=headers,
            json={"username": "newname"},
        )

        # Assert
        assert_error_response(response, expected_status=401)

    def test_update_other_user_forbidden(
        self,
        client: FlaskClient,
        clean_db: Generator[Session, None, None],
    ):
        """
        タスク2.7: 他ユーザーのプロフィール更新で403エラーになることを検証する

        ユーザーAのトークンでユーザーBのプロフィールを更新しようとする
        レスポンスが403ステータスコードであることを確認

        Requirements: 2.8
        """
        # Arrange
        user_a = make_and_save_user(
            clean_db,
            username="userA",
            email="userA@example.com",
            password="password123",
        )
        user_b = make_and_save_user(
            clean_db,
            username="userB",
            email="userB@example.com",
            password="password123",
        )

        access_token = make_access_token(user_a.user_id)
        headers = make_api_headers()
        headers["Authorization"] = f"Bearer {access_token}"

        # Act: ユーザーAのトークンでユーザーBのプロフィールを更新
        response = client.patch(
            f"/api/v1/users/{user_b.user_id}",
            headers=headers,
            json={"username": "newname"},
        )

        # Assert
        assert_error_response(response, expected_status=403)

    def test_update_empty_request_body_error(
        self,
        client: FlaskClient,
        authenticated_user: dict,
    ):
        """
        タスク2.8: 空のリクエストボディで400エラーになることを検証する

        空のJSONでPATCHリクエストを送信する
        レスポンスが400ステータスコードであることを確認

        Requirements: 2.9
        """
        # Arrange
        user = authenticated_user["user"]
        headers = authenticated_user["headers"]

        # Act: 空のリクエストボディを送信（data=Noneで空ボディ）
        response = client.patch(
            f"/api/v1/users/{user.user_id}",
            headers=headers,
            data=None,
            content_type="application/json",
        )

        # Assert
        assert_error_response(response, expected_status=400)


@pytest.mark.api
@pytest.mark.auth
class TestPartialUpdate:
    """部分更新機能のテスト (Task 3)"""

    def test_partial_update_username_only(
        self,
        client: FlaskClient,
        authenticated_user: dict,
    ):
        """
        タスク3.1: ユーザー名のみを更新し、他のフィールドが変更されないことを確認

        ユーザー名のみを更新し、他のフィールドが変更されないことを確認
        メールアドレスのみを更新し、他のフィールドが変更されないことを確認

        Requirements: 3.1
        """
        # Arrange
        user = authenticated_user["user"]
        headers = authenticated_user["headers"]
        original_email = user.email
        original_currency = user.base_currency
        new_username = "partially_updated"

        # Act: ユーザー名のみを更新
        response = client.patch(
            f"/api/v1/users/{user.user_id}",
            headers=headers,
            json={"username": new_username},
        )

        # Assert
        data = assert_success_response(response, expected_status=200)
        profile = data["data"]
        assert profile["username"] == new_username
        assert profile["email"] == original_email
        assert profile["base_currency"] == original_currency

    def test_partial_update_email_only(
        self,
        client: FlaskClient,
        authenticated_user: dict,
    ):
        """
        タスク3.1: メールアドレスのみを更新し、他のフィールドが変更されないことを確認

        Requirements: 3.1
        """
        # Arrange
        user = authenticated_user["user"]
        headers = authenticated_user["headers"]
        original_username = user.username
        original_currency = user.base_currency
        new_email = "partial_update@example.com"

        # Act: メールアドレスのみを更新
        response = client.patch(
            f"/api/v1/users/{user.user_id}",
            headers=headers,
            json={"email": new_email},
        )

        # Assert
        data = assert_success_response(response, expected_status=200)
        profile = data["data"]
        assert profile["email"] == new_email
        assert profile["username"] == original_username
        assert profile["base_currency"] == original_currency

    def test_empty_object_no_changes(
        self,
        client: FlaskClient,
        authenticated_user: dict,
    ):
        """
        タスク3.2: 空のオブジェクトでプロフィールが変更されないことを検証する

        空のJSONオブジェクト`{}`でPATCHリクエストを送信する
        現在のプロフィール情報が変更されずに返されることを確認

        Requirements: 3.2
        """
        # Arrange
        user = authenticated_user["user"]
        headers = authenticated_user["headers"]
        original_username = user.username
        original_email = user.email
        original_currency = user.base_currency

        # Act: 空のJSONオブジェクトを送信
        response = client.patch(
            f"/api/v1/users/{user.user_id}",
            headers=headers,
            json={},  # 空のオブジェクト
        )

        # Assert
        data = assert_success_response(response, expected_status=200)
        profile = data["data"]
        assert profile["username"] == original_username
        assert profile["email"] == original_email
        assert profile["base_currency"] == original_currency


@pytest.mark.api
@pytest.mark.auth
class TestDeleteUser:
    """DELETE /api/v1/users/{userId} エンドポイントのテスト"""

    def test_delete_user_success(
        self,
        client: FlaskClient,
        clean_db: Generator[Session, None, None],
    ):
        """
        タスク4.1: 正常系 204 No Content返却

        有効なJWTトークンと正しいパスワードでDELETEリクエストを送信
        レスポンスが204ステータスコードであることを確認

        Requirements: 1.1, 1.2, 2.1, 2.2
        """
        # Arrange
        user = make_and_save_user(
            clean_db,
            username="deleteuser",
            email="delete@example.com",
            password="correct_password123",
        )
        access_token = make_access_token(user.user_id)
        headers = make_api_headers()
        headers["Authorization"] = f"Bearer {access_token}"

        # Act
        response = client.delete(
            f"/api/v1/users/{user.user_id}",
            headers=headers,
            json={"password": "correct_password123"},
        )

        # Assert
        assert response.status_code == 204

    def test_delete_user_unauthorized(
        self,
        client: FlaskClient,
        clean_db: Generator[Session, None, None],
    ):
        """
        タスク4.1: 認証エラー 401 Unauthorized

        JWTトークンなしでDELETEリクエストを送信
        レスポンスが401ステータスコードであることを確認

        Requirements: 3.1
        """
        # Arrange
        user = make_and_save_user(clean_db)
        headers = {"Content-Type": "application/json"}

        # Act
        response = client.delete(
            f"/api/v1/users/{user.user_id}",
            headers=headers,
            json={"password": "any_password"},
        )

        # Assert
        assert_error_response(response, expected_status=401)

    def test_delete_other_user_forbidden(
        self,
        client: FlaskClient,
        clean_db: Generator[Session, None, None],
    ):
        """
        タスク4.1: 認可エラー 403 Forbidden

        ユーザーAのトークンでユーザーBの削除を試みる
        レスポンスが403ステータスコードであることを確認

        Requirements: 3.2
        """
        # Arrange
        user_a = make_and_save_user(
            clean_db,
            username="userA",
            email="userA@example.com",
            password="password123",
        )
        user_b = make_and_save_user(
            clean_db,
            username="userB",
            email="userB@example.com",
            password="password123",
        )

        access_token = make_access_token(user_a.user_id)
        headers = make_api_headers()
        headers["Authorization"] = f"Bearer {access_token}"

        # Act: ユーザーAのトークンでユーザーBを削除
        response = client.delete(
            f"/api/v1/users/{user_b.user_id}",
            headers=headers,
            json={"password": "password123"},
        )

        # Assert
        assert_error_response(response, expected_status=403)

    def test_delete_user_password_missing(
        self,
        client: FlaskClient,
        clean_db: Generator[Session, None, None],
    ):
        """
        タスク4.1: バリデーションエラー 400 Bad Request (パスワード未指定)

        パスワードなしでDELETEリクエストを送信
        レスポンスが400ステータスコードであることを確認

        Requirements: 2.3
        """
        # Arrange
        user = make_and_save_user(clean_db)
        access_token = make_access_token(user.user_id)
        headers = make_api_headers()
        headers["Authorization"] = f"Bearer {access_token}"

        # Act
        response = client.delete(
            f"/api/v1/users/{user.user_id}",
            headers=headers,
            json={},  # パスワードなし
        )

        # Assert
        assert_error_response(response, expected_status=400)

    def test_delete_user_invalid_password(
        self,
        client: FlaskClient,
        clean_db: Generator[Session, None, None],
    ):
        """
        タスク4.1: バリデーションエラー 400 Bad Request (パスワード不一致)

        間違ったパスワードでDELETEリクエストを送信
        レスポンスが400ステータスコードであることを確認

        Requirements: 2.2
        """
        # Arrange
        user = make_and_save_user(
            clean_db,
            username="invalidpassuser",
            email="invalidpass@example.com",
            password="correct_password",
        )
        access_token = make_access_token(user.user_id)
        headers = make_api_headers()
        headers["Authorization"] = f"Bearer {access_token}"

        # Act
        response = client.delete(
            f"/api/v1/users/{user.user_id}",
            headers=headers,
            json={"password": "wrong_password"},
        )

        # Assert
        assert_error_response(response, expected_status=400)

    def test_delete_user_not_found(
        self,
        client: FlaskClient,
        clean_db: Generator[Session, None, None],
    ):
        """
        タスク4.1: 存在エラー 404 Not Found

        存在しないユーザーIDでDELETEリクエストを送信
        レスポンスが404ステータスコードであることを確認
        ※ 非存在ユーザーのトークンを使用して認可チェックを通過させる

        Requirements: 1.3
        """
        # Arrange
        nonexistent_user_id = 99999
        access_token = make_access_token(nonexistent_user_id)
        headers = make_api_headers()
        headers["Authorization"] = f"Bearer {access_token}"

        # Act
        response = client.delete(
            f"/api/v1/users/{nonexistent_user_id}",
            headers=headers,
            json={"password": "any_password"},
        )

        # Assert
        assert_error_response(response, expected_status=404)


@pytest.mark.api
@pytest.mark.auth
class TestDeleteUserCascade:
    """ユーザー削除時のカスケード削除テスト"""

    def test_delete_user_cascades_subscriptions(
        self,
        client: FlaskClient,
        clean_db: Generator[Session, None, None],
    ):
        """
        タスク6.1: ユーザー削除後のsubscriptions削除確認

        ユーザー削除時にサブスクリプションが削除されることを確認
        Requirements: 4.1
        """
        # Arrange
        from app.models.label import Label
        from app.models.subscription import Subscription

        user = make_and_save_user(
            clean_db,
            username="cascadeuser",
            email="cascade@example.com",
            password="password123",
        )
        subscription = make_and_save_subscription(clean_db, user_id=user.user_id)

        access_token = make_access_token(user.user_id)
        headers = make_api_headers()
        headers["Authorization"] = f"Bearer {access_token}"

        # Act
        response = client.delete(
            f"/api/v1/users/{user.user_id}",
            headers=headers,
            json={"password": "password123"},
        )

        # Assert
        assert response.status_code == 204

        # Verify subscription was deleted
        remaining_subscriptions = clean_db.query(Subscription).filter_by(
            user_id=user.user_id
        ).all()
        assert len(remaining_subscriptions) == 0

    def test_delete_user_cascades_labels(
        self,
        client: FlaskClient,
        clean_db: Generator[Session, None, None],
    ):
        """
        タスク6.1: ユーザー削除後のlabels削除確認

        ユーザー削除時にラベルが削除されることを確認
        Requirements: 4.2
        """
        # Arrange
        from app.models.label import Label

        user = make_and_save_user(
            clean_db,
            username="labeluser",
            email="labeluser@example.com",
            password="password123",
        )
        label = make_and_save_label(clean_db, user_id=user.user_id)

        access_token = make_access_token(user.user_id)
        headers = make_api_headers()
        headers["Authorization"] = f"Bearer {access_token}"

        # Act
        response = client.delete(
            f"/api/v1/users/{user.user_id}",
            headers=headers,
            json={"password": "password123"},
        )

        # Assert
        assert response.status_code == 204

        # Verify label was deleted
        remaining_labels = clean_db.query(Label).filter_by(
            user_id=user.user_id
        ).all()
        assert len(remaining_labels) == 0

    def test_delete_user_cascades_payment_histories(
        self,
        client: FlaskClient,
        clean_db: Generator[Session, None, None],
    ):
        """
        タスク6.1: ユーザー削除後のpayment_histories削除確認

        ユーザー削除時に支払い履歴が削除されることを確認
        Requirements: 4.3
        """
        # Arrange
        from datetime import date

        from app.models.payment_history import PaymentHistory
        from app.models.subscription import Subscription

        user = make_and_save_user(
            clean_db,
            username="paymentuser",
            email="paymentuser@example.com",
            password="password123",
        )
        subscription = make_and_save_subscription(
            clean_db, user_id=user.user_id, name="Test Sub"
        )

        # Create exchange rate for payment history
        from tests.helpers import make_and_save_exchange_rate

        make_and_save_exchange_rate(
            clean_db,
            from_currency="JPY",
            to_currency="JPY",
            date=date(2024, 1, 1),
            rate=1.0,
        )

        # Create payment history
        payment_history = PaymentHistory(
            user_id=user.user_id,
            subscription_id=subscription.subscription_id,
            subscription_name=subscription.name,
            payment_date=date(2024, 1, 1),
            amount=1000,
            currency="JPY",
            rate_from_currency="JPY",
            rate_to_currency="JPY",
            rate_date=date(2024, 1, 1),
            exchange_rate=1.0,
            converted_amount=1000,
            payment_method="credit_card",
        )
        clean_db.add(payment_history)
        clean_db.commit()

        access_token = make_access_token(user.user_id)
        headers = make_api_headers()
        headers["Authorization"] = f"Bearer {access_token}"

        # Act
        response = client.delete(
            f"/api/v1/users/{user.user_id}",
            headers=headers,
            json={"password": "password123"},
        )

        # Assert
        assert response.status_code == 204

        # Verify payment history was deleted
        remaining_histories = clean_db.query(PaymentHistory).filter_by(
            user_id=user.user_id
        ).all()
        assert len(remaining_histories) == 0
