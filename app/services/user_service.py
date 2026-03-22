"""
ユーザープロフィールサービス
"""

from typing import Any

from sqlalchemy.orm import Session

from app.models.user import User
from app.repositories.user_repository import UserRepository


class UserService:
    """ユーザープロフィール関連のビジネスロジックを提供する"""

    VALID_CURRENCIES = {"JPY", "USD", "EUR", "GBP"}

    def __init__(self, session: Session) -> None:
        self.repository = UserRepository(session)

    def get_user_by_id(self, user_id: int) -> User | None:
        """ユーザーIDでユーザーを取得する"""
        return self.repository.find_by_id(user_id)

    def update_user(self, user_id: int, data: dict[str, Any]) -> User:
        """ユーザー情報を更新する"""
        user = self.repository.find_by_id(user_id)
        if not user:
            raise ValueError("ユーザーが見つかりません")

        # 更新可能なフィールド
        if "username" in data:
            username = data["username"].strip() if data["username"] else None
            if username:
                user.username = username

        if "email" in data:
            email = data["email"].strip() if data["email"] else None
            if email:
                # メールの重複チェック
                existing = User.query.filter(
                    User.email == email,
                    User.user_id != user_id,
                ).first()
                if existing:
                    raise ValueError("このメールアドレスは既に使用されています")
                user.email = email

        if "base_currency" in data:
            base_currency = data["base_currency"]
            if base_currency and base_currency not in self.VALID_CURRENCIES:
                raise ValueError(f"無効な通貨コードです: {base_currency}")
            if base_currency:
                user.base_currency = base_currency

        return self.repository.save(user)
