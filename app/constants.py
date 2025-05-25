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
