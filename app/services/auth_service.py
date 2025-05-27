from typing import Optional
from app.models.user import User
from app.models import db
from app.constants import ErrorMessages
from werkzeug.security import generate_password_hash
from sqlalchemy.exc import IntegrityError

class AuthService:
    def authenticate(self, email: str, password: str) -> Optional[User]:
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            return user
        return None

    def register_user(self, data: dict) -> User:
        if data.get("password") != data.get("confirm_password"):
            raise ValueError("Passwords do not match")

        existing_user = User.query.filter(
            (User.email == data.get("email")) | (User.username == data.get("username"))
        ).first()
        if existing_user:
            raise ValueError(ErrorMessages.DUPLICATE_SUBSCRIPTION)  # 適切なエラーメッセージに変更可能

        user = User(
            username=data.get("username"),
            email=data.get("email"),
        )
        user.set_password(data.get("password"))

        db.session.add(user)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            raise ValueError(ErrorMessages.DUPLICATE_SUBSCRIPTION)

        return user
