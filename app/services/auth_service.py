import json
import re
from pathlib import Path

from sqlalchemy.exc import IntegrityError

from app.constants import ErrorMessages, ValidationConstants
from app.models import db
from app.models.user import User
from app.services.label_service import LabelService


class AuthService:
    """Service for authentication-related operations."""

    def authenticate(self, email: str, password: str) -> User | None:
        """
        Authenticate user with email and password.

        Args:
            email: User's email address.
            password: User's password.

        Returns:
            User instance if authentication successful, None otherwise.
        """
        if not email or not password:
            return None

        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            return user
        return None

    def register_user(self, data: dict) -> User:
        """
        Register a new user with validation.

        Args:
            data: Registration data dictionary containing username, email, password, etc.

        Returns:
            User: Created user instance.

        Raises:
            ValueError: If validation fails or user already exists.
        """
        # Extract and clean input data
        username = data.get("username", "").strip()
        email = data.get("email", "").strip()
        password = data.get("password", "")
        confirm_password = data.get("confirm_password", "")

        # Validate username
        self._validate_username(username)

        # Validate email
        self._validate_email(email)

        # Validate password
        self._validate_password(password)

        # Validate password confirmation
        if password != confirm_password:
            raise ValueError(ErrorMessages.PASSWORDS_DO_NOT_MATCH)

        # Check for existing users (separate checks for better error messages)
        self._check_username_availability(username)
        self._check_email_availability(email)

        # Create new user
        user = User(
            username=username,
            email=email,
        )
        user.set_password(password)

        # Save to database
        db.session.add(user)
        try:
            # コミット前にデフォルトラベルを登録するためにflushを使ってuser_idを取得可能にする
            db.session.flush()

            # デフォルトラベルをJSONから読み込み、登録する
            default_labels_path = Path("instance/default_labels.json")
            if default_labels_path.exists():
                with default_labels_path.open(encoding="utf-8") as f:
                    default_labels = json.load(f)
            else:
                default_labels = []

            label_service = LabelService(db.session)
            for label_data in default_labels:
                label_service.create_label(user.user_id, label_data)

            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            # This shouldn't happen if our checks above are correct,
            # but handle it just in case
            msg = "User registration failed due to database constraint"
            raise ValueError(msg) from IntegrityError

        return user

    def _validate_username(self, username: str) -> None:
        """
        Validate username according to business rules.

        Args:
            username: Username to validate.

        Raises:
            ValueError: If username is invalid.
        """
        if not username:
            raise ValueError(ErrorMessages.USERNAME_EMPTY)

        if len(username) < ValidationConstants.USERNAME_MIN_LENGTH:
            raise ValueError(ErrorMessages.USERNAME_TOO_SHORT)

        if len(username) > ValidationConstants.USERNAME_MAX_LENGTH:
            raise ValueError(ErrorMessages.USERNAME_TOO_LONG)

        # Check if username is only whitespace
        if not username.strip():
            raise ValueError(ErrorMessages.USERNAME_EMPTY)

    def _validate_email(self, email: str) -> None:
        """
        Validate email format according to business rules.

        Args:
            email: Email to validate.

        Raises:
            ValueError: If email is invalid.
        """
        if not email:
            raise ValueError(ErrorMessages.EMAIL_EMPTY)

        # Basic email format validation using constant pattern
        if not re.match(ValidationConstants.EMAIL_PATTERN, email):
            raise ValueError(ErrorMessages.EMAIL_INVALID_FORMAT)

    def _validate_password(self, password: str) -> None:
        """
        Validate password according to business rules.

        Args:
            password: Password to validate.

        Raises:
            ValueError: If password is invalid.
        """
        if not password:
            raise ValueError(ErrorMessages.PASSWORD_EMPTY)

        if len(password) < ValidationConstants.PASSWORD_MIN_LENGTH:
            raise ValueError(ErrorMessages.PASSWORD_TOO_SHORT)

    def _check_username_availability(self, username: str) -> None:
        """
        Check if username is available.

        Args:
            username: Username to check.

        Raises:
            ValueError: If username is already taken.
        """
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            raise ValueError(ErrorMessages.DUPLICATE_USERNAME)

    def _check_email_availability(self, email: str) -> None:
        """
        Check if email is available.

        Args:
            email: Email to check.

        Raises:
            ValueError: If email is already taken.
        """
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            raise ValueError(ErrorMessages.DUPLICATE_EMAIL)
