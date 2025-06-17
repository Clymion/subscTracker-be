"""
定数定義モジュール
"""


class ValidationConstants:
    """
    バリデーション関連の定数クラス。
    """

    # Username validation
    USERNAME_MIN_LENGTH = 3
    USERNAME_MAX_LENGTH = 32

    # Password validation
    PASSWORD_MIN_LENGTH = 8

    # Email validation pattern
    EMAIL_PATTERN = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"


class CurrencyConstants:
    """
    通貨関連の定数クラス。
    """

    # Supported currencies (only USD and JPY)
    USD = "USD"
    JPY = "JPY"

    @classmethod
    def all(cls) -> list[str]:
        """Return all supported currency codes."""
        return [cls.USD, cls.JPY]

    @classmethod
    def is_valid(cls, currency: str) -> bool:
        """Check if currency code is supported."""
        return currency.upper() in cls.all()


class SubscriptionStatus:
    """
    サブスクリプションステータス定数クラス。
    """

    TRIAL = "trial"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    CANCELLED = "cancelled"
    EXPIRED = "expired"

    @classmethod
    def all(cls) -> list[str]:
        """Return all valid subscription statuses."""
        return [cls.TRIAL, cls.ACTIVE, cls.SUSPENDED, cls.CANCELLED, cls.EXPIRED]

    @classmethod
    def is_valid(cls, status: str) -> bool:
        """Check if status is valid."""
        return status in cls.all()


class PaymentFrequency:
    """
    支払頻度定数クラス。
    """

    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"

    @classmethod
    def all(cls) -> list[str]:
        """Return all valid payment frequencies."""
        return [cls.MONTHLY, cls.QUARTERLY, cls.YEARLY]

    @classmethod
    def is_valid(cls, frequency: str) -> bool:
        """Check if payment frequency is valid."""
        return frequency in cls.all()


class PaymentMethods:
    """
    支払方法定数クラス。
    """

    CREDIT_CARD = "credit_card"
    BANK_TRANSFER = "bank_transfer"
    PAYPAL = "paypal"
    APPLE_PAY = "apple_pay"
    GOOGLE_PAY = "google_pay"

    @classmethod
    def all(cls) -> list[str]:
        """Return all valid payment methods."""
        return [
            cls.CREDIT_CARD,
            cls.BANK_TRANSFER,
            cls.PAYPAL,
            cls.APPLE_PAY,
            cls.GOOGLE_PAY,
        ]

    @classmethod
    def is_valid(cls, method: str) -> bool:
        """Check if payment method is valid."""
        return method in cls.all()


from typing import ClassVar


class LabelConstants:
    """
    ラベル関連の定数クラス。
    """

    # Maximum hierarchy depth
    MAX_HIERARCHY_DEPTH = 5

    # Default system label names
    DEFAULT_LABELS: ClassVar[list[str]] = [
        "Entertainment",
        "Productivity",
        "Education",
        "Health",
        "Finance",
        "Shopping",
        "Communication",
        "Development",
    ]

    # Default colors for system labels (hex format)
    DEFAULT_COLORS: ClassVar[list[str]] = [
        "#FF6B6B",  # Red
        "#4ECDC4",  # Teal
        "#45B7D1",  # Blue
        "#96CEB4",  # Green
        "#FFEAA7",  # Yellow
        "#DDA0DD",  # Plum
        "#98D8C8",  # Mint
        "#F7DC6F",  # Light Yellow
    ]


class ErrorMessages:
    """
    集中管理されたエラーメッセージ定数クラス。

    すべてのエラーメッセージはここで定義し、他のモジュールからインポートして利用すること。
    """

    # Authentication errors
    INVALID_CREDENTIALS = "The provided credentials are invalid"
    USER_NOT_FOUND = "User not found"
    INSUFFICIENT_PERMISSIONS = "You do not have permission to access this resource"
    TOKEN_EXPIRED = "Authentication token has expired"  # noqa: S105

    # Subscription errors
    SUBSCRIPTION_NOT_FOUND = "Subscription not found"
    DUPLICATE_SUBSCRIPTION = "A subscription with this name already exists"
    INVALID_SUBSCRIPTION_STATUS = "Invalid subscription status"
    INVALID_CURRENCY = "Invalid currency code. Supported currencies: USD, JPY"
    INVALID_PAYMENT_FREQUENCY = "Invalid payment frequency"

    # Subscription validation errors
    UNSUPPORTED_CURRENCY = "Unsupported currency"
    INVALID_STATUS = "Invalid status"
    PRICE_MUST_BE_POSITIVE = "Price must be positive"
    NEXT_PAYMENT_DATE_BEFORE_INITIAL = (
        "Next payment date cannot be before initial payment date"
    )
    UNKNOWN_PAYMENT_FREQUENCY = "Unknown payment frequency"
    CANNOT_DELETE_LABEL_WITH_CHILDREN = "Cannot delete a label that has child labels"

    # Label errors
    LABEL_NOT_FOUND = "Label not found"
    DUPLICATE_LABEL = "A label with this name already exists"
    INVALID_LABEL_COLOR = "Invalid color format. Use hex format (e.g., #FFFFFF)"
    LABEL_HIERARCHY_TOO_DEEP = (
        f"Label hierarchy cannot exceed {LabelConstants.MAX_HIERARCHY_DEPTH} levels"
    )
    CIRCULAR_REFERENCE = "Circular reference detected in label hierarchy"
    SYSTEM_LABEL_READONLY = "System labels cannot be modified or deleted"

    # Label validation errors
    LABEL_NAME_REQUIRED = "Label name is required"
    LABEL_COLOR_REQUIRED = "Label color is required"
    INVALID_HEX_COLOR = "Invalid hex color format"
    LABEL_NAME_TOO_LONG = "Label name is too long"

    # Payment errors
    PAYMENT_FAILED = "Payment processing failed"
    INVALID_PAYMENT_METHOD = "Invalid payment method"

    # General errors
    BAD_REQUEST = "Bad request"
    NOT_FOUND = "Resource not found"
    UNAUTHORIZED = "Unauthorized access"
    FORBIDDEN = "Forbidden access"

    # Pagination errors
    PAGINATION_LIMIT_OFFSET_NOT_INTEGER = "limit and offset must be integers"
    PAGINATION_LIMIT_OUT_OF_RANGE = "limit must be between 0 and {max_limit}"
    PAGINATION_OFFSET_NEGATIVE = "offset must be non-negative"

    # User validation errors
    USERNAME_TOO_SHORT = f"Username must be at least {ValidationConstants.USERNAME_MIN_LENGTH} characters long"
    USERNAME_TOO_LONG = f"Username must be no more than {ValidationConstants.USERNAME_MAX_LENGTH} characters long"
    USERNAME_EMPTY = "Username is required"
    EMAIL_INVALID_FORMAT = "Invalid email format"
    EMAIL_EMPTY = "Email is required"
    PASSWORD_TOO_SHORT = f"Password must be at least {ValidationConstants.PASSWORD_MIN_LENGTH} characters long"
    PASSWORD_EMPTY = "Password is required"  # noqa: S105
    PASSWORDS_DO_NOT_MATCH = "Passwords do not match"
    DUPLICATE_USERNAME = "A user with this username already exists"
    DUPLICATE_EMAIL = "A user with this email already exists"
