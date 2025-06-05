# Test List: Subscription Service

## Feature Description
Business logic service for subscription management including CRUD operations, validation, and business rules enforcement.

## Related Requirements
- REQ-SERV-001: Users can only access their own subscriptions
- REQ-SERV-002: Prevent duplicate subscription names per user
- REQ-SERV-003: Validate subscription data before persistence
- REQ-SERV-004: Enforce business rules for status transitions
- REQ-SERV-005: Calculate payment dates automatically

## Test Categories

### Unit Tests

#### SubscriptionService Setup
- [ ] Test SubscriptionService initialization with database session
- [ ] Test SubscriptionService initialization with repository dependency
- [ ] Test service instance creation is successful

#### Create Subscription (create_subscription)
- [ ] Test create_subscription with valid data creates subscription
- [ ] Test create_subscription sets correct user_id
- [ ] Test create_subscription with duplicate name raises DuplicateSubscriptionError (case-insensitive)
- [ ] Test create_subscription validates required fields
- [ ] Test create_subscription validates price is positive (REAL type)
- [ ] Test create_subscription validates currency format (USD or JPY only)
- [ ] Test create_subscription calculates next_payment_date correctly (smart month-end)
- [ ] Test create_subscription with labels assigns labels correctly
- [ ] Test create_subscription with invalid user_id raises SubscriptionNotFoundError
- [ ] Test create_subscription with invalid status raises validation error
- [ ] Test create_subscription accepts any valid status value from constants enum
- [ ] Test create_subscription transaction rollback on validation failure

#### Get Subscription (get_subscription)
- [ ] Test get_subscription returns correct subscription by ID
- [ ] Test get_subscription raises SubscriptionNotFoundError for non-existent ID
- [ ] Test get_subscription validates user ownership
- [ ] Test get_subscription denies access to other user's subscription
- [ ] Test get_subscription returns subscription with all relationships

#### Get Subscriptions List (get_subscriptions_by_user)
- [ ] Test get_subscriptions_by_user returns all user subscriptions
- [ ] Test get_subscriptions_by_user returns empty list for user with no subscriptions
- [ ] Test get_subscriptions_by_user filters by status correctly
- [ ] Test get_subscriptions_by_user filters by currency correctly (USD or JPY)
- [ ] Test get_subscriptions_by_user filters by labels correctly
- [ ] Test get_subscriptions_by_user sorting by name works
- [ ] Test get_subscriptions_by_user sorting by price works
- [ ] Test get_subscriptions_by_user sorting by next_payment_date works
- [ ] Test get_subscriptions_by_user pagination works correctly
- [ ] Test get_subscriptions_by_user excludes other users' subscriptions

#### Update Subscription (update_subscription)
- [ ] Test update_subscription updates fields correctly
- [ ] Test update_subscription validates user ownership
- [ ] Test update_subscription prevents duplicate names
- [ ] Test update_subscription validates new data
- [ ] Test update_subscription updates next_payment_date when frequency changes
- [ ] Test update_subscription accepts any valid status change (user-driven)
- [ ] Test update_subscription does not enforce status transition rules
- [ ] Test update_subscription updates labels correctly
- [ ] Test update_subscription raises error for non-existent subscription
- [ ] Test update_subscription denies access to other user's subscription
- [ ] Test update_subscription with partial data updates only specified fields

#### Delete Subscription (delete_subscription)
- [ ] Test delete_subscription performs hard deletion (complete removal)
- [ ] Test delete_subscription validates user ownership
- [ ] Test delete_subscription raises SubscriptionNotFoundError for non-existent subscription
- [ ] Test delete_subscription denies access to other user's subscription
- [ ] Test delete_subscription removes label relationships (cascade deletion)
- [ ] Test delete_subscription updates label usage counts in transaction
- [ ] Test delete_subscription transaction rollback on failure

#### Business Logic Methods
- [ ] Test calculate_total_monthly_cost returns correct sum
- [ ] Test calculate_total_yearly_cost returns correct sum
- [ ] Test get_active_subscriptions filters by status='active'
- [ ] Test get_trial_subscriptions filters by status='trial'
- [ ] Test get_subscriptions_by_status filters by any given status
- [ ] Test get_subscriptions_by_label filters correctly
- [ ] Test validate_status_value checks against constants enum values
- [ ] Test recalculate_payment_dates with smart month-end handling

### Integration Tests

#### Service-Repository Integration
- [ ] Test SubscriptionService correctly uses SubscriptionRepository
- [ ] Test service-level transactions are handled properly (commit/rollback)
- [ ] Test service handles repository-level database errors gracefully
- [ ] Test service commits transactions only on complete success
- [ ] Test service rolls back transactions on any validation failure
- [ ] Test service handles concurrent access safely
- [ ] Test service maintains transaction boundaries across multiple repository calls

#### Service-Model Integration
- [ ] Test service creates valid Subscription model instances
- [ ] Test service handles model validation errors
- [ ] Test service propagates model validation to caller
- [ ] Test service handles relationship loading correctly

#### Multiple User Scenarios
- [ ] Test multiple users can have subscriptions with same name
- [ ] Test user isolation - users cannot access each other's data
- [ ] Test concurrent access by different users
- [ ] Test service maintains data integrity across users

### Business Rule Testing

#### Validation Rules
- [ ] Test duplicate name validation per user with case-insensitive comparison
- [ ] Test price validation (positive, REAL type compatibility)
- [ ] Test currency code validation (USD or JPY only, uppercase normalization)
- [ ] Test payment frequency validation (values from constants enum)
- [ ] Test date validation (initial_payment_date, next_payment_date logic)
- [ ] Test status validation against constants enum (no transition rules)
- [ ] Test business rule: subscription name uniqueness per user

#### Status Management Rules
- [ ] Test status validation accepts any valid enum value from constants
- [ ] Test status can be changed from any status to any other valid status
- [ ] Test status change is user-driven, not automatic
- [ ] Test invalid status values are rejected with validation error
- [ ] Test status field is always required (cannot be null or empty)
- [ ] Test status values from constants: 'trial', 'active', 'suspended', 'cancelled', 'expired'
- [ ] Test status-specific business logic (if any) in separate methods
- [ ] Test status change does not trigger automatic field updates

#### Payment Date Calculations
- [ ] Test monthly payment date calculation with smart month-end handling
- [ ] Test quarterly payment date calculation with smart month-end handling
- [ ] Test yearly payment date calculation with smart month-end handling
- [ ] Test payment date calculation with edge cases (Feb 29 → Feb 28)
- [ ] Test payment date calculation preserves month-end contracts
- [ ] Test payment date recalculation when frequency changes
- [ ] Test payment date validation (cannot be in the past for active subscriptions)

### Error Handling Tests

#### Validation Errors
- [ ] Test service raises SubscriptionError for invalid input data
- [ ] Test service raises DuplicateSubscriptionError for name conflicts
- [ ] Test service raises validation error for invalid status values
- [ ] Test service provides meaningful error messages
- [ ] Test service validates all required fields
- [ ] Test service handles edge cases gracefully

#### Database Errors
- [ ] Test service handles database connection errors
- [ ] Test service handles constraint violation errors
- [ ] Test service handles transaction timeout errors
- [ ] Test service maintains data consistency on errors

#### Authorization Errors
- [ ] Test service raises SubscriptionNotFoundError for unauthorized access
- [ ] Test service error messages don't leak sensitive information
- [ ] Test service validates user permissions consistently
- [ ] Test service handles cross-user access attempts appropriately

### Performance Tests
- [ ] Test service performance with large number of subscriptions
- [ ] Test filtering and sorting performance with large datasets
- [ ] Test service handles concurrent requests efficiently

## Integration with Existing Systems

### Authentication Integration
- [ ] Test service works with existing JWT authentication
- [ ] Test service uses current user context correctly
- [ ] Test service integrates with auth middleware properly

### Error Handling Integration
- [ ] Test service uses centralized error messages (ErrorMessages constants)
- [ ] Test service error format matches existing error patterns
- [ ] Test service integrates with common error handlers

## Implementation Approach
1. Create SubscriptionService in `app/services/subscription_service.py`
2. Follow existing AuthService patterns and conventions
3. Implement business logic methods with proper validation
4. Create SubscriptionRepository in `app/repositories/subscription_repository.py`
5. Write comprehensive unit tests following this test list
6. Test integration with existing authentication system

## Dependencies
- Subscription model (from previous test list)
- User model (existing)
- Database session management
- Authentication service integration

## Estimated Effort
Large (8-13 story points)

## Acceptance Criteria
- [ ] All service tests pass with 90%+ coverage
- [ ] Service enforces all business rules correctly
- [ ] Service integrates properly with existing authentication
- [ ] Service handles errors gracefully with meaningful messages
- [ ] Service follows existing code patterns and conventions

## Design Decisions (RESOLVED)
1. **Repository Pattern**: ✅ Use separate repository classes
2. **Transaction Management**: ✅ Service-level transactions
3. **Error Handling**: ✅ Custom exceptions with meaningful messages
4. **Validation Strategy**: ✅ Service-level validation (comprehensive)
5. **Caching Strategy**: ✅ No caching in initial implementation
6. **Duplicate Names**: ✅ Per-user uniqueness with case-insensitive comparison
7. **Deletion Policy**: ✅ Hard deletion (complete removal)

## Additional Implementation Requirements

### Custom Exceptions
```python
# Define in app/exceptions.py
class SubscriptionError(Exception): pass
class SubscriptionNotFoundError(SubscriptionError): pass
class DuplicateSubscriptionError(SubscriptionError): pass
class ValidationError(SubscriptionError): pass  # For general validation errors
```

### Transaction Management Pattern
- Use service-level transactions for complex operations
- Implement proper rollback on any validation failure
- Handle nested service calls carefully

### Validation Strategy
- Primary validation at service layer
- Model validation as secondary safety net
- Business rule validation in service methods

### Currency Support
- Support only USD and JPY currencies
- Validate currency codes in uppercase format
- Store currency validation rules in constants.py

## Implementation Status
Ready to start - all design decisions resolved
