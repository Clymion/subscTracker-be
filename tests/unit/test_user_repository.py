"""
UserRepositoryの単体テスト

DELETE /api/v1/users/{userId} 機能に関連するリポジトリ層のテスト
"""

from unittest.mock import MagicMock

import pytest

from app.models.user import User
from app.repositories.user_repository import UserRepository


@pytest.fixture
def mock_session():
    """モックセッションの作成"""
    session = MagicMock()
    return session


@pytest.fixture
def user_repository(mock_session):
    """UserRepositoryのインスタンス"""
    return UserRepository(mock_session)


@pytest.fixture
def sample_user():
    """サンプルユーザー"""
    user = User(user_id=1, username="testuser", email="test@example.com")
    user.set_password("testpassword123")
    return user


class TestUserRepositoryDelete:
    """UserRepository.deleteのテスト"""

    def test_delete_user_success(self, user_repository, mock_session, sample_user):
        """
        正常系: ユーザー削除成功

        ユーザーを削除し、セッションから削除されることを確認
        Requirements: 4.1, 4.2, 4.3, 4.4
        """
        # Act
        user_repository.delete(sample_user)

        # Assert
        mock_session.delete.assert_called_once_with(sample_user)
        mock_session.commit.assert_called_once()

    def test_delete_user_removes_from_session(
        self, user_repository, mock_session, sample_user
    ):
        """
        正常系: セッションからユーザーが削除されることを確認

        deleteメソッドがsession.delete(user)を呼び出すことを確認
        Requirements: 4.1, 4.2, 4.3, 4.4
        """
        # Act
        user_repository.delete(sample_user)

        # Assert
        mock_session.delete.assert_called_once()
        call_args = mock_session.delete.call_args
        assert call_args[0][0] == sample_user

    def test_delete_user_commits_transaction(
        self, user_repository, mock_session, sample_user
    ):
        """
        正常系: トランザクションがコミットされることを確認

        deleteメソッドがsession.commit()を呼び出すことを確認
        Requirements: 4.1, 4.2, 4.3, 4.4
        """
        # Act
        user_repository.delete(sample_user)

        # Assert
        mock_session.commit.assert_called_once()

    def test_delete_user_with_db_error(
        self, user_repository, mock_session, sample_user
    ):
        """
        異常系: データベースエラー時の挙動

        データベースエラーが発生した場合、例外が伝播することを確認
        Requirements: 5.1
        """
        # Arrange
        mock_session.delete.side_effect = Exception("Database error")

        # Act & Assert
        with pytest.raises(Exception, match="Database error"):
            user_repository.delete(sample_user)
