# Code Structure and Quality

## Type Hints

All functions and methods **must** use type hints for arguments and return values. Use built-in types for collections instead of typing-specific imports like `typing.List`.

```python
# Good
def get_subscription(subscription_id: str) -> dict:
    pass

def get_subscriptions_by_user(user_id: str) -> list[dict]:
    pass

# Avoid
from typing import List, Dict
def get_subscriptions_by_user(user_id: str) -> List[Dict]:
    pass
```

### Type Hint Best Practices

- Always specify return types, including `None` when appropriate
- Use `T | None` for parameters that might be None
- Use `T1 | T2` for parameters that might be multiple types
- Leverage `TypedDict` for dictionary structures with known keys
- Use `Literal` types for constrained string options

### RESTful Endpoint Guidelines

- Use plural nouns for resource collections (`/subscriptions`)
- Use HTTP methods appropriately:
  - `GET` - Retrieve resources
  - `POST` - Create resources
  - `PUT` - Replace resources
  - `PATCH` - Update resources
  - `DELETE` - Remove resources
- Return appropriate HTTP status codes:
  - `200` - Success
  - `201` - Created
  - `204` - No Content
  - `400` - Bad Request
  - `401` - Unauthorized
  - `403` - Forbidden
  - `404` - Not Found
  - `500` - Server Error

## JWT Authentication

Implement authentication using flask-jwt-extended. Use `@jwt_required()` decorator for protected endpoints.

```python
from flask_jwt_extended import jwt_required, get_jwt_identity

@subscription_bp.route('/<subscription_id>', methods=['GET'])
@jwt_required()
def get_subscription(subscription_id: str):
    current_user = get_jwt_identity()
    # Implementation
    return jsonify(result), 200
```

### Authentication Configuration

- Store JWT secret key in environment variables
- Configure reasonable token expiration times
- Implement refresh token mechanism for long-lived sessions
- Maintain a token blacklist for revoked tokens


## Code Quality Tools

- **Ruff**: For linting and style checking
- **Black**: For code formatting
- **isort**: For import sorting
- **pytest**: For testing

Configure pre-commit hooks to run these tools automatically before commits.


# Python Best Practices

## Function and Method Design

### Pure Functions

Prefer pure functions (those without side effects) when possible:

```python
# Good: Pure function
def calculate_price(base_price: float, tax_rate: float) -> float:
    return base_price * (1 + tax_rate)

# Avoid: Function with side effects
def calculate_and_update_price(product, tax_rate: float) -> None:
    product.price = product.base_price * (1 + tax_rate)
```

### Function Arguments

- Limit the number of function parameters (ideally 4 or fewer)
- Use keyword arguments for functions with many parameters
- Order parameters with positional-only first, then regular, then keyword-only
- Use `*args` and `**kwargs` only when necessary for flexibility

```python
def get_subscriptions(
    user_id: str,
    *,
    status: Optional[str] = None,
    start_date: Optional[date] = None,
    limit: int = 100,
    offset: int = 0
) -> list[dict]:
    """Get user subscriptions with optional filtering."""
    # Implementation
```

## Docstrings

Use Google-style docstrings for all public modules, classes, and functions:

```python
def register_user(username: str, email: str, password: str) -> dict:
    """Register a new user in the system.

    This function creates a new user account with the provided information,
    hashes the password for secure storage, and returns the created user.

    Args:
        username: The desired username.
        email: The user's email address.
        password: The plaintext password (will be hashed).

    Returns:
        A dictionary containing the created user's information.

    Raises:
        ValueError: If the username or email is already taken.
        ValidationError: If any input fails validation.
    """
    # Implementation
```

## Error Handling

### Exception Types

- Raise specific exceptions rather than generic ones
- Create custom exception classes for domain-specific errors
- Use built-in exceptions appropriately:
  - `ValueError` for invalid values
  - `TypeError` for wrong type
  - `KeyError` for missing keys
  - `IndexError` for out-of-range indices
  - `FileNotFoundError` for missing files
  - `PermissionError` for permission issues

### Exception Handling

- Only catch specific exceptions, not `Exception`
- Handle exceptions as close to their source as possible
- Use the `with` statement for resource management
- Include context information in exception messages

```python
# Good
try:
    user = get_user_by_id(user_id)
except UserNotFoundError as e:
    logger.warning(f"User lookup failed: {e}")
    raise HTTPNotFoundError(f"User with ID {user_id} not found") from e

# Avoid
try:
    user = get_user_by_id(user_id)
except Exception as e:
    logger.error(f"Error: {e}")
    raise
```

## Constants and Configuration

- Define constants at the module level using `UPPER_CASE_NAMES`
- Use `constants.py` for project-wide constants
- Use environment variables for configuration
- Centralize error messages

```python
# app/constants.py
class ErrorMessages:
    INVALID_CREDENTIALS = "The provided credentials are invalid"
    USER_NOT_FOUND = "User not found"
    INSUFFICIENT_PERMISSIONS = "You do not have permission to access this resource"

# Using error messages
from app.constants import ErrorMessages

def authenticate_user(username: str, password: str) -> dict:
    user = get_user(username)
    if not user:
        raise APIError(ErrorMessages.USER_NOT_FOUND, 404)
    if not check_password(user, password):
        raise APIError(ErrorMessages.INVALID_CREDENTIALS, 401)
    return user
```

## Code Organization

### Module Structure

- Keep modules focused on a single responsibility
- Use clear, descriptive module names
- Organize imports properly (standard library, third-party, local)
- Implement `__all__` for controlling public API
- Follow the "Rule of 7": a module should contain no more than 7 classes/functions

### Naming Conventions

- Classes: `PascalCase`
- Functions/Methods: `snake_case`
- Variables: `snake_case`
- Constants: `UPPER_SNAKE_CASE`
- Private attributes/methods: `_leading_underscore`
- Protected attributes/methods: `__double_leading_underscore`

## Testing

### Test Structure

- Use pytest for all testing
- Create test fixtures for reusable test setup
- Properly annotate test fixtures
- Use descriptive test names (test_when_X_then_Y)
- Keep tests independent and idempotent

```python
import pytest
from app.models.user import User

@pytest.fixture
def test_user() -> User:
    """Create a test user for testing."""
    return User(
        id="test-id-123",
        username="testuser",
        email="test@example.com",
        role="user"
    )

def test_when_username_valid_then_user_created(test_user: User) -> None:
    """Test that a user is created successfully with valid username."""
    assert test_user.username == "testuser"
    assert test_user.email == "test@example.com"
```

### Test Coverage

- Aim for 90%+ code coverage
- Test happy paths, error paths, and edge cases
- Use parameterized tests for testing multiple inputs
- Mock external dependencies

## Security Practices

- Never hardcode sensitive information (passwords, API keys, etc.)
- Use environment variables for configuration
- Always validate user input
- Use parameterized queries to prevent SQL injection
- Hash passwords with appropriate algorithms (bcrypt)
- Implement proper access control
- Log security-relevant events

## Performance Considerations

- Use generators for large data sets
- Avoid unnecessary computation in loops
- Use database-level operations when possible
- Consider caching for expensive operations
- Profile performance of critical code paths
- Use appropriate data structures for operations
