# Test Driven Development (TDD) Workflow

## Core TDD Principle

TDD follows the "Red-Green-Refactor" cycle:
1. Write a failing test (Red)
2. Write the minimal code to make the test pass (Green)
3. Refactor the code while keeping tests passing (Refactor)

## Test List First Approach

**CRITICAL**: Before starting implementation, always create a test list for each feature.

### Test List Creation Process

1. For each feature, first create a comprehensive test list document
2. Save the test list in the `/docs/test-list/` directory
3. Review and get approval of the test list before starting implementation
4. Use the test list as a development guide and checklist

### Test List Format

Test lists should use the following structure:

```markdown
# Feature: [Feature Name]

## Description
[Brief description of the feature]

## Test Cases

### Unit Tests
- [ ] Test [function/method] with valid inputs
- [ ] Test [function/method] with invalid inputs
- [ ] Test [edge case description]
...

### Integration Tests
- [ ] Test [component A] with [component B]
- [ ] Test [error handling between components]
...

### API Tests
- [ ] Test [endpoint] with valid request
- [ ] Test [endpoint] with invalid request
- [ ] Test [endpoint] authentication requirements
...

## Implementation Plan
1. [Implementation step 1]
2. [Implementation step 2]
...
```

### Example Test List

```markdown
# Feature: User Subscription Management

## Description
API endpoints and business logic to allow users to create, view, update and delete their subscriptions.

## Test Cases

### Unit Tests
- [ ] Test Subscription model validation with valid input
- [ ] Test Subscription model validation with missing required fields
- [ ] Test SubscriptionService.create_subscription with valid input
- [ ] Test SubscriptionService.create_subscription with duplicate subscription name
- [ ] Test SubscriptionService.get_subscription with existing subscription
- [ ] Test SubscriptionService.get_subscription with non-existent subscription
- [ ] Test SubscriptionService.update_subscription with valid updates
- [ ] Test SubscriptionService.delete_subscription successfully removes subscription
- [ ] Test SubscriptionCollection.active_subscriptions correctly filters
- [ ] Test SubscriptionCollection.total_monthly_cost calculates correctly

### Integration Tests
- [ ] Test subscription creation flow from controller to database
- [ ] Test subscription retrieval flow with database
- [ ] Test subscription update with validation and persistence
- [ ] Test subscription deletion with cascading effects

### API Tests
- [ ] Test GET /api/v1/subscriptions/ returns 200 and list of subscriptions
- [ ] Test GET /api/v1/subscriptions/ with pagination parameters
- [ ] Test GET /api/v1/subscriptions/<id> returns 200 and subscription details
- [ ] Test GET /api/v1/subscriptions/<id> returns 404 for non-existent subscription
- [ ] Test POST /api/v1/subscriptions/ with valid payload returns 201
- [ ] Test POST /api/v1/subscriptions/ with invalid payload returns 400
- [ ] Test PUT /api/v1/subscriptions/<id> with valid payload returns 200
- [ ] Test DELETE /api/v1/subscriptions/<id> returns 204
- [ ] Test all endpoints correctly enforce authentication
- [ ] Test endpoints enforce authorization (users can only access their own subscriptions)

## Implementation Plan
1. Create Subscription model and validations
2. Implement SubscriptionService with core business logic
3. Create SubscriptionCollection value object
4. Implement REST API controllers using Flask
5. Connect controllers to service layer
6. Implement authentication and authorization
```

## Detailed TDD Workflow

1. **Create Test List**:
   - Identify all features needed for the current sprint/task
   - For each feature, create a detailed test list document
   - Save it to `./docs/test-list/{feature-name}.md`
   - Get test list approval from team lead or peer review

2. **Implement Tests**:
   - Follow the test list order (generally unit → integration → API)
   - Write each test before implementing the corresponding code
   - Ensure each test fails first (Red)

3. **Implement Code**:
   - Write minimal code to make the current test pass
   - Avoid implementing features not covered by tests
   - Maintain the discipline of writing tests first

4. **Refactor**:
   - Clean up code after tests pass
   - Maintain test coverage during refactoring
   - Update test list with any additional tests identified

5. **Document Progress**:
   - Mark completed tests in the test list
   - Update the test list with any changes to requirements
   - Keep test list as living documentation

## Test Structure

### Using pytest

```python
import pytest
from app.models import Subscription
from app.services import SubscriptionService
from datetime import datetime

@pytest.fixture
def sample_subscription():
    return Subscription(
        id="test-id-123",
        name="Netflix Premium",
        user_id="user-1",
        created_at=datetime.utcnow()
    )

def test_subscription_creation(sample_subscription):
    assert sample_subscription.id == "test-id-123"
    assert sample_subscription.name == "Netflix Premium"
    assert sample_subscription.user_id == "user-1"
    assert isinstance(sample_subscription.created_at, datetime)

def test_subscription_service_create(db_session, sample_user):
    service = SubscriptionService(db_session)
    sub_data = {
        "name": "Disney+",
        "price": 7.99,
        "billing_cycle": "monthly"
    }

    subscription = service.create_subscription(sample_user.id, sub_data)

    assert subscription.name == "Disney+"
    assert subscription.price == 7.99
    assert subscription.user_id == sample_user.id
    assert subscription.id is not None
```

## API Testing

```python
def test_get_subscriptions_api(client, auth_tokens):
    headers = {"Authorization": f"Bearer {auth_tokens['access_token']}"}
    response = client.get("/api/v1/subscriptions/", headers=headers)

    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    if len(data) > 0:
        assert "id" in data[0]
        assert "name" in data[0]
```

## Coverage Requirements

- Maintain a minimum of 90% test coverage for all code
- 100% coverage for core business logic and models
- Track coverage with pytest-cov and generate reports
- Include coverage reports in CI/CD pipeline
