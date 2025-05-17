# Project Rules

## Centralized Constants and Master Data

Define all constants and master data in a dedicated `constants.py` file to ensure consistency throughout the application.

```python
# app/constants.py

class SubscriptionStatus:
    ACTIVE = "active"
    CANCELLED = "cancelled"
    SUSPENDED = "suspended"
    PENDING = "pending"
    EXPIRED = "expired"

    @classmethod
    def all(cls) -> list[str]:
        """Return all valid subscription statuses."""
        return [cls.ACTIVE, cls.CANCELLED, cls.SUSPENDED, cls.PENDING, cls.EXPIRED]

class PaymentMethods:
    CREDIT_CARD = "credit_card"
    BANK_TRANSFER = "bank_transfer"
    PAYPAL = "paypal"

    @classmethod
    def all(cls) -> list[str]:
        """Return all valid payment methods."""
        return [cls.CREDIT_CARD, cls.BANK_TRANSFER, cls.PAYPAL]

class ErrorMessages:
    # Authentication errors
    INVALID_CREDENTIALS = "The provided credentials are invalid"
    USER_NOT_FOUND = "User not found"
    INSUFFICIENT_PERMISSIONS = "You do not have permission to access this resource"
    TOKEN_EXPIRED = "Authentication token has expired"

    # Subscription errors
    SUBSCRIPTION_NOT_FOUND = "Subscription not found"
    DUPLICATE_SUBSCRIPTION = "A subscription with this name already exists"
    INVALID_SUBSCRIPTION_STATUS = "Invalid subscription status"

    # Payment errors
    PAYMENT_FAILED = "Payment processing failed"
    INVALID_PAYMENT_METHOD = "Invalid payment method"
```

## Error Message Management

Always import error messages from the central constants file when raising exceptions:

```python
# Using error messages
from app.constants import ErrorMessages

def authenticate_user(username: str, password: str) -> dict:
    user = get_user(username)
    if not user:
        raise APIError(ErrorMessages.USER_NOT_FOUND, 404)
    if not check_password(user, password):
        raise APIError(ErrorMessages.INVALID_CREDENTIALS, the401)
    return user
```

### Error Response Format

Standardize all API error responses with this format:

```json
{
  "error": {
    "code": "USER_NOT_FOUND",
    "message": "User not found",
    "details": {
      "user_id": "The provided user ID does not exist"
    }
  }
}
```

## Logging Standards

Use a consistent logging approach throughout the application:

```python
import logging
from app.constants import LoggingCategories

logger = logging.getLogger(__name__)

def process_subscription(subscription_id: str) -> None:
    """Process a subscription payment."""
    logger.info(
        f"Processing subscription {subscription_id}",
        extra={
            "category": LoggingCategories.PAYMENT,
            "subscription_id": subscription_id
        }
    )

    try:
        # Implementation
        logger.info(
            f"Successfully processed subscription {subscription_id}",
            extra={
                "category": LoggingCategories.PAYMENT,
                "subscription_id": subscription_id
            }
        )
    except Exception as e:
        logger.error(
            f"Failed to process subscription {subscription_id}: {str(e)}",
            extra={
                "category": LoggingCategories.PAYMENT,
                "subscription_id": subscription_id,
                "error": str(e)
            },
            exc_info=True
        )
        raise
```

## Configuration Management

Use a centralized configuration system:

```python
# app/config.py
import os
from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class AppConfig:
    """Application configuration."""
    # Database settings
    DB_HOST: str
    DB_PORT: int
    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str

    # API settings
    API_PORT: int = 5000
    DEBUG: bool = False

    # JWT settings
    JWT_SECRET_KEY: str
    JWT_ACCESS_TOKEN_EXPIRES: int = 3600  # 1 hour
    JWT_REFRESH_TOKEN_EXPIRES: int = 2592000  # 30 days

    # Feature flags
    ENABLE_NEW_BILLING: bool = False

    @classmethod
    def from_env(cls) -> 'AppConfig':
        """Create configuration from environment variables."""
        return cls(
            DB_HOST=os.getenv('DB_HOST', 'localhost'),
            DB_PORT=int(os.getenv('DB_PORT', '5432')),
            DB_NAME=os.getenv('DB_NAME', 'app_db'),
            DB_USER=os.getenv('DB_USER', 'postgres'),
            DB_PASSWORD=os.getenv('DB_PASSWORD', ''),
            API_PORT=int(os.getenv('API_PORT', '5000')),
            DEBUG=os.getenv('DEBUG', 'False').lower() == 'true',
            JWT_SECRET_KEY=os.getenv('JWT_SECRET_KEY', ''),
            JWT_ACCESS_TOKEN_EXPIRES=int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', '3600')),
            JWT_REFRESH_TOKEN_EXPIRES=int(os.getenv('JWT_REFRESH_TOKEN_EXPIRES', '2592000')),
            ENABLE_NEW_BILLING=os.getenv('ENABLE_NEW_BILLING', 'False').lower() == 'true',
        )

# Create configuration once at application startup
config = AppConfig.from_env()
```

## Service Layer Pattern

Use service layer pattern for all business logic:

```python
# app/services/subscription_service.py
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session

from app.constants import ErrorMessages, SubscriptionStatus
from app.exceptions import APIError
from app.models.subscription import Subscription
from app.repositories.subscription_repository import SubscriptionRepository

class SubscriptionService:
    """Service for subscription-related operations."""

    def __init__(self, session: Session):
        self.session = session
        self.subscription_repository = SubscriptionRepository(session)

    def create_subscription(self, user_id: str, data: dict) -> Subscription:
        """Create a new subscription."""
        # Check for existing subscription with same name
        existing = self.subscription_repository.find_by_user_and_name(
            user_id=user_id,
            name=data['name']
        )
        if existing:
            raise APIError(ErrorMessages.DUPLICATE_SUBSCRIPTION, 400)

        # Create subscription
        subscription = Subscription(
            user_id=user_id,
            name=data['name'],
            status=SubscriptionStatus.ACTIVE,
            created_at=datetime.utcnow()
        )

        return self.subscription_repository.save(subscription)
```

## Repository Pattern

Use repository pattern for all database access:

```python
# app/repositories/subscription_repository.py
from typing import Optional, List
from sqlalchemy.orm import Session

from app.models.subscription import Subscription

class SubscriptionRepository:
    """Repository for subscription data access."""

    def __init__(self, session: Session):
        self.session = session

    def find_by_id(self, subscription_id: str) -> Optional[Subscription]:
        """Find a subscription by ID."""
        return self.session.query(Subscription).filter(
            Subscription.id == subscription_id
        ).first()

    def find_by_user_id(self, user_id: str) -> List[Subscription]:
        """Find all subscriptions for a user."""
        return self.session.query(Subscription).filter(
            Subscription.user_id == user_id
        ).all()

    def find_by_user_and_name(self, user_id: str, name: str) -> Optional[Subscription]:
        """Find a subscription by user ID and name."""
        return self.session.query(Subscription).filter(
            Subscription.user_id == user_id,
            Subscription.name == name
        ).first()

    def save(self, subscription: Subscription) -> Subscription:
        """Save a subscription."""
        self.session.add(subscription)
        self.session.commit()
        return subscription

    def delete(self, subscription: Subscription) -> None:
        """Delete a subscription."""
        self.session.delete(subscription)
        self.session.commit()
```

## Schema Validation

Use validation schemas for all API input:

```python
# app/schemas/subscription.py
from marshmallow import Schema, fields, validate

from app.constants import SubscriptionStatus

class CreateSubscriptionSchema(Schema):
    """Schema for creating a subscription."""
    name = fields.String(required=True, validate=validate.Length(min=1, max=100))
    price = fields.Float(required=True, validate=validate.Range(min=0))
    billing_cycle = fields.String(required=True, validate=validate.OneOf(
        ['monthly', 'quarterly', 'yearly']
    ))

class UpdateSubscriptionSchema(Schema):
    """Schema for updating a subscription."""
    name = fields.String(validate=validate.Length(min=1, max=100))
    price = fields.Float(validate=validate.Range(min=0))
    billing_cycle = fields.String(validate=validate.OneOf(
        ['monthly', 'quarterly', 'yearly']
    ))
    status = fields.String(validate=validate.OneOf(SubscriptionStatus.all()))
```

## Commit Message Guidelines

Use the following format for all commit messages:

```
{type}({scope}): {message}
```

Example:
```
feat(subscription): add recurring billing feature
fix(auth): resolve token expiration issue
docs(api): update OpenAPI documentation
```

## Testing Rules

- All code must have tests
- Test coverage must be at least 90%
- All tests must pass before merging
- Create a test list document before implementing each feature
- TDD approach: write tests first, then code
