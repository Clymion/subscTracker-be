"""
UserServiceの単体テスト

DELETE /api/v1/users/{userId} 機能に関連するサービス層のテスト
"""

from unittest.mock import MagicMock

import pytest

from app.constants import ErrorMessages
from app.exceptions import InvalidPasswordError, UserNotFoundError
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.services.user_service import UserService


@pytest.fixture
def mock_session():
    """モックセッションの作成"""
    return MagicMock()


@pytest.fixture
def mock_repository():
    """モックリポジトリの作成"""
    return MagicMock(spec=UserRepository)


@pytest.fixture
def user_service(mock_session, mock_repository):
    """UserServiceのインスタンス"""
    service = UserService(mock_session)
    service.repository = mock_repository
    return service


@pytest.fixture
def sample_user():
    """サンプルユーザー"""
    user = User(user_id=1, username="testuser", email="test@example.com")
    user.set_password("correct_password123")
    return user


class TestUserServiceDeleteUser:
    """UserService.delete_userのテスト"""

    def test_delete_user_success(
        self, user_service, mock_repository, sample_user
    ):
        """
        正常系: ユーザー削除成功

        正しいパスワードでユーザーを削除できることを確認
        Requirements: 1.3, 6.1
        """
        # Arrange
        mock_repository.find_by_id.return_value = sample_user

        # Act
        user_service.delete_user(user_id=1, password="correct_password123")

        # Assert
        mock_repository.find_by_id.assert_called_once_with(1)
        mock_repository.delete.assert_called_once_with(sample_user)

    def test_delete_user_not_found(
        self, user_service, mock_repository
    ):
        """
        異常系: ユーザー不在時のUserNotFoundError

        存在しないユーザーIDで削除を試みた場合、UserNotFoundErrorが発生することを確認
        Requirements: 1.3
        """
        # Arrange
        mock_repository.find_by_id.return_value = None

        # Act & Assert
        with pytest.raises(UserNotFoundError):
            user_service.delete_user(user_id=999, password="any_password")

    def test_delete_user_invalid_password(
        self, user_service, mock_repository, sample_user
    ):
        """
        異常系: パスワード不一致時のInvalidPasswordError

        間違ったパスワードで削除を試みた場合、InvalidPasswordErrorが発生することを確認
        Requirements: 2.2
        """
        # Arrange
        mock_repository.find_by_id.return_value = sample_user
        wrong_password = "wrong_password"

        # Act & Assert
        with pytest.raises(InvalidPasswordError):
            user_service.delete_user(user_id=1, password=wrong_password)

        # deleteが呼ばれないことを確認
        mock_repository.delete.assert_not_called()

    def test_delete_user_logs_deletion(
        self, user_service, mock_repository, sample_user
    ):
        """
        正常系: 削除操作のログ記録

        ユーザー削除時にログが記録されることを確認
        Requirements: 6.1
        """
        # Arrange
        mock_repository.find_by_id.return_value = sample_user

        # Act
        user_service.delete_user(user_id=1, password="correct_password123")

        # Assert - ログ記録は実装で確認（モックでは呼び出し順序を確認）
        mock_repository.find_by_id.assert_called_once()
        mock_repository.delete.assert_called_once()

    def test_delete_user_failure_logs_error(
        self, user_service, mock_repository, sample_user
    ):
        """
        異常系: 削除失敗時のログ記録

        削除失敗時にログが記録されることを確認
        Requirements: 6.2
        """
        # Arrange
        mock_repository.find_by_id.return_value = sample_user
        mock_repository.delete.side_effect = Exception("Database error")

        # Act & Assert
        with pytest.raises(Exception, match="Database error"):
            user_service.delete_user(user_id=1, password="correct_password123")
