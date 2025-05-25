# Object-Oriented Design Principles

## Complete Constructor Pattern

Always ensure objects are fully initialized and valid at creation time. Avoid creating "half-baked" objects that require additional setup after instantiation.

```python
class User:
    def __init__(self, user_id: str, username: str, email: str, role: str):
        self.id = user_id
        self.username = username
        self.email = email
        self.role = role
        # All required fields are set in constructor
        # Object is ready to use immediately after creation
```

### Key Benefits

- Ensures objects are always in a valid state
- Eliminates temporal coupling
- Makes the code more predictable and easier to reason about
- Prevents bugs from partially initialized objects

### Implementation Guidelines

- Make all parameters required that are necessary for object validity
- Use optional parameters with default values for non-required fields
- Perform all validation in the constructor
- Raise clear exceptions for invalid parameters
- Don't expose setters for required attributes

## Value Objects

Implement immutable value objects for conceptual wholes. Value objects:
- Are equality-comparable based on their attributes, not identity
- Are immutable
- Have no side effects
- Encapsulate domain rules about the values

```python
from dataclasses import dataclass
from datetime import date
from typing import Optional

@dataclass(frozen=True)  # frozen=True makes it immutable
class DateRange:
    start_date: date
    end_date: date

    def __post_init__(self):
        # Validation logic in __post_init__ for frozen dataclasses
        if self.start_date > self.end_date:
            raise ValueError("Start date must be before or equal to end date")

    @property
    def days(self) -> int:
        return (self.end_date - self.start_date).days + 1

    def overlaps_with(self, other: 'DateRange') -> bool:
        return self.start_date <= other.end_date and other.start_date <= self.end_date
```

### When To Use Value Objects

- When equality should be based on all attributes, not object identity
- For domain concepts that are defined by their attributes
- For immutable concepts that represent a value rather than an entity
- To encapsulate validation and business rules about a value

### Common Value Object Examples

- DateRange
- Money
- EmailAddress
- PhoneNumber
- Address
- Coordinates
- Temperature

## First-Class Collections

Wrap collections in dedicated classes to enforce business rules and provide domain-specific operations.


### Benefits of First-Class Collections

- Encapsulate business logic related to the collection
- Prevent duplicate code through centralized implementation
- Improve code readability through domain-specific operations
- Enable adding invariants and validation logic at the collection level
- Makes it easier to refactor collection implementations


## Domain-Driven Design

Organize code around business domain concepts, using bounded contexts to manage complexity.

- **Entities**: Objects defined by their identity (e.g., User)
- **Value Objects**: Objects defined by their attributes (e.g., Address)
- **Aggregates**: Clusters of entities and value objects treated as a unit
- **Repositories**: Objects that handle persistence of aggregates
- **Services**: Objects that encapsulate domain operations that don't belong to entities
- **Factories**: Objects that create complex entities and aggregates

Follow ubiquitous language principles by using consistent terminology across the codebase that matches business domain language.


# Architecture Principles

## Layered Architecture

The application follows a layered architecture pattern with clear separation of concerns:

```
┌─────────────────┐
│     API Layer   │  HTTP interface, request/response handling
├─────────────────┤
│  Service Layer  │  Business logic, transactions, coordination
├─────────────────┤
│ Repository Layer│  Data access, persistence
├─────────────────┤
│    Data Layer   │  Database, external services
└─────────────────┘
```

### Layer Responsibilities

1. **API Layer**
   - Handle HTTP requests and responses
   - Parse and validate input
   - Serialize output
   - Handle authentication and authorization
   - Route to appropriate service

2. **Service Layer**
   - Implement business logic
   - Coordinate multiple operations
   - Manage transactions
   - Enforce business rules
   - Orchestrate complex workflows

3. **Repository Layer**
   - Abstract data access
   - Implement CRUD operations
   - Handle database-specific concerns
   - Provide domain objects to services

4. **Data Layer**
   - Database tables and relationships
   - External service integrations
   - File storage

### Layer Rules

- Each layer can only depend on layers below it
- Layers should not be skipped (API cannot call Repository directly)
- Higher layers should not know implementation details of lower layers
- Each layer has its own models/DTOs for data transfer

## Domain-Driven Design Concepts

### Entities

Objects with a distinct identity that runs through time and different states:

```python
class User:
    def __init__(self, user_id: str, username: str, email: str):
        self.id = user_id  # Identity field
        self.username = username
        self.email = email
```

### Value Objects

Immutable objects that represent descriptive aspects of the domain:

```python
@dataclass(frozen=True)
class Money:
    amount: Decimal
    currency: str

    def __add__(self, other: 'Money') -> 'Money':
        if self.currency != other.currency:
            raise ValueError("Cannot add different currencies")
        return Money(amount=self.amount + other.amount, currency=self.currency)
```

### Aggregates

Cluster of domain objects that can be treated as a single unit:

```python
class Order:  # Aggregate root
    def __init__(self, order_id: str, customer_id: str):
        self.id = order_id
        self.customer_id = customer_id
        self._items: list[OrderItem] = []  # Part of the aggregate

    def add_item(self, product_id: str, quantity: int, price: Money) -> None:
        # Business logic validations
        if quantity <= 0:
            raise ValueError("Quantity must be positive")

        # Creating child entity within the aggregate
        item = OrderItem(
            order_id=self.id,
            product_id=product_id,
            quantity=quantity,
            price=price
        )
        self._items.append(item)

    def total(self) -> Money:
        # Calculating across the aggregate
        if not self._items:
            return Money(amount=Decimal('0'), currency='USD')

        currency = self._items[0].price.currency
        total_amount = sum(item.price.amount * item.quantity for item in self._items)
        return Money(amount=total_amount, currency=currency)
```

### Domain Services

Operations that don't belong to any entity or value object:

```python
class PaymentProcessingService:
    def __init__(self, payment_gateway: PaymentGateway):
        self.payment_gateway = payment_gateway

    def process_payment(self, order: Order, payment_method: PaymentMethod) -> PaymentResult:
        # Complex domain logic that doesn't belong to any single entity
        # Involves multiple aggregates and external services
        amount = order.total()
        return self.payment_gateway.charge(payment_method, amount, order.id)
```

### Event-Driven Architecture

Use events for loose coupling between components:

```python
# Event definition
@dataclass(frozen=True)
class UserRegisteredEvent:
    user_id: str
    email: str
    timestamp: datetime

# Event publisher
class EventPublisher:
    def __init__(self):
        self.subscribers: dict[type, list[Callable]] = {}

    def subscribe(self, event_type: type, handler: Callable) -> None:
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(handler)

    def publish(self, event: Any) -> None:
        event_type = type(event)
        if event_type in self.subscribers:
            for handler in self.subscribers[event_type]:
                handler(event)

# Event handler
def send_welcome_email(event: UserRegisteredEvent) -> None:
    # Send welcome email implementation

# Event usage
publisher = EventPublisher()
publisher.subscribe(UserRegisteredEvent, send_welcome_email)

# When user registers
user = create_user(...)
publisher.publish(UserRegisteredEvent(
    user_id=user.id,
    email=user.email,
    timestamp=datetime.utcnow()
))
```
