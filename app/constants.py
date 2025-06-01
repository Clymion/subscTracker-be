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
