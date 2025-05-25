# Documentation Guidelines

## Documentation Locations

All project documentation should be maintained in appropriate locations:

- **OpenAPI Definition**: `/docs/openapi/`
- **Database Definitions**: `/docs/db/`
- **Test Lists**: `/docs/test-list/`
- **Feature Documentation**: `/docs/features/`
- **Architecture Documentation**: `/docs/architecture/`

## Code Documentation

### Docstrings

All modules, classes, methods, and functions must have appropriate docstrings following the Google style:

```python
def get_user_subscriptions(user_id: str, status: Optional[str] = None) -> list[dict]:
    """Retrieves subscriptions for a specific user.

    This function queries the database for all subscriptions belonging
    to the specified user. Results can be filtered by subscription status.

    Args:
        user_id: The unique identifier of the user.
        status: Optional filter for subscription status.
            Valid values are 'active', 'cancelled', 'pending'.

    Returns:
        A list of dictionaries containing subscription details.

    Raises:
        ValueError: If the provided status is not valid.
        UserNotFoundError: If no user exists with the given user_id.
    """
    # Implementation
```

### Module-Level Documentation

Each module should have a module-level docstring describing its purpose:

```python
"""
Subscription service module.

This module contains the business logic for managing user subscriptions.
It provides functionality for creating, updating, and cancelling subscriptions,
as well as handling subscription payments and notifications.
"""
```

### Class Documentation

```python
class SubscriptionService:
    """Provides business logic for subscription management.

    This service handles all subscription-related operations including
    creation, modification, cancellation, and billing cycles.

    Attributes:
        db_session: The database session for persistence operations.
        notifier: The notification service for sending updates.
    """
```

## API Documentation

### OpenAPI Specification

Maintain an up-to-date OpenAPI specification in `/docs/openapi/`. This can be generated automatically from code annotations, but should be manually reviewed and enhanced.

```python
@subscription_bp.route('/<subscription_id>', methods=['GET'])
@jwt_required()
def get_subscription(subscription_id: str):
    """Get a specific subscription.
    ---
    tags:
      - subscriptions
    parameters:
      - name: subscription_id
        in: path
        required: true
        schema:
          type: string
    responses:
      200:
        description: Subscription found
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/Subscription'
      404:
        description: Subscription not found
    security:
      - BearerAuth: []
    """
    # Implementation
```

## Database Documentation

### Table Definitions

Document all database tables in `/docs/db/table-definition.md`:

```markdown
# Database Tables

## Subscriptions

Stores user subscription information.

| Column      | Type         | Constraints      | Description                   |
|-------------|--------------|------------------|-------------------------------|
| id          | VARCHAR(36)  | PK, NOT NULL     | Unique subscription ID (UUID) |
| user_id     | VARCHAR(36)  | FK, NOT NULL     | Reference to users table      |
| name        | VARCHAR(100) | NOT NULL         | Subscription name             |
| status      | VARCHAR(20)  | NOT NULL         | Subscription status           |
| created_at  | TIMESTAMP    | NOT NULL         | Creation timestamp            |
| updated_at  | TIMESTAMP    | NOT NULL         | Last update timestamp         |

**Indexes:**
- `idx_subscription_user_id`: Index on `user_id` column
- `idx_subscription_status`: Index on `status` column

**Foreign Keys:**
- `fk_subscription_user`: `user_id` references `users(id)` ON DELETE CASCADE
```

### Entity Relationship Diagrams

Include ERD diagrams in `/docs/db/` to visualize database relationships. Update these diagrams whenever the database schema changes.

## Test Documentation

### Test Lists

Create detailed test lists in `/docs/test-list/` before implementing features. For format, see the TDD workflow document.

### Test Documentation Comments

Include clear documentation in test files:

```python
def test_subscription_cancellation():
    """
    Test Scenario: User cancels an active subscription

    Given: A user with an active subscription
    When: The user requests to cancel the subscription
    Then:
      - The subscription status should change to 'cancelled'
      - The cancellation_date should be set
      - The user should not be billed again
    """
    # Test implementation
```

## Architectural Documentation

### Component Diagrams

Maintain up-to-date component diagrams showing the relationships between major system components.

### Sequence Diagrams

Create sequence diagrams for complex flows to illustrate the interactions between components.

## Markdown Style Guide

Follow these guidelines for all markdown documentation:

- Use ATX-style headings (with `#` symbols)
- Use code blocks with language specification
- Use tables for structured data
- Use bullet points for lists of items
- Use numbered lists for sequential steps
- Include a table of contents for longer documents
- Link between related documents
