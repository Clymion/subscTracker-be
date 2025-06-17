# Test List: Subscription Model

## Feature Description
SQLAlchemy model for subscription management with validation, relationships, and business logic.

## Related Requirements
- REQ-SUBSC-001: Subscription must belong to a specific user
- REQ-SUBSC-002: Subscription must have required fields (name, price, currency, etc.)
- REQ-SUBSC-003: Subscription status must be valid enum value
- REQ-SUBSC-004: Next payment date calculation based on frequency
- REQ-SUBSC-005: Support for labels (many-to-many relationship)

## Test Categories

### Unit Tests

#### Model Creation and Validation
- [ ] Test Subscription creation with all required fields
- [ ] Test Subscription creation with minimal required fields
- [ ] Test Subscription creation with all optional fields
- [ ] Test default values are applied correctly (created_at, updated_at)
- [ ] Test model attributes are correctly assigned
- [ ] Test string representation (__repr__) returns expected format

#### Field Validation
- [ ] Test name field validation (required, max length)
- [ ] Test price field validation (required, positive number, REAL type for SQLite3)
- [ ] Test currency field validation (required, USD or JPY only)
- [ ] Test payment_frequency validation (valid enum values from constants)
- [ ] Test payment_method validation (valid enum values from constants)
- [ ] Test status validation (valid enum values from constants, transition rules)
- [ ] Test URL field validation (optional, basic URL format check)
- [ ] Test image_url field validation (optional, basic URL format check)
- [ ] Test notes field validation (optional, max length)

#### Date Field Validation
- [ ] Test initial_payment_date validation (required, valid date)
- [ ] Test next_payment_date validation (required, valid date)
- [ ] Test next_payment_date cannot be before initial_payment_date
- [ ] Test created_at and updated_at are stored as TEXT in UTC format
- [ ] Test date parsing from TEXT to datetime objects correctly

#### Relationship Validation
- [ ] Test user relationship (foreign key constraint)
- [ ] Test user relationship returns correct User object
- [ ] Test subscription belongs to correct user
- [ ] Test labels relationship (many-to-many)
- [ ] Test adding labels to subscription
- [ ] Test removing labels from subscription

#### Business Logic Methods
- [ ] Test is_active() method returns correct boolean based on status (no soft delete check)
- [ ] Test calculate_next_payment_date() for monthly frequency with smart month-end handling
- [ ] Test calculate_next_payment_date() for quarterly frequency with smart month-end handling
- [ ] Test calculate_next_payment_date() for yearly frequency with smart month-end handling
- [ ] Test calculate_next_payment_date() handles edge cases (Feb 29 → Feb 28, Jan 31 → Feb 28/29)
- [ ] Test monthly_cost() calculation for different frequencies
- [ ] Test yearly_cost() calculation for different frequencies

#### Status Management
- [ ] Test status field accepts valid enum values from constants.py
- [ ] Test status field rejects invalid values (not in constants enum)
- [ ] Test status can be freely set by user input (no automatic transitions)
- [ ] Test status change does not automatically update other fields
- [ ] Test status validation uses constants enum for allowed values
- [ ] Test status field is required and cannot be null
- [ ] Test status enum values are properly defined in constants.py
- [ ] Test status field stores exactly what user provides (after validation)

### Integration Tests

#### Database Operations
- [ ] Test subscription saves to database correctly with REAL price type
- [ ] Test subscription retrieval from database
- [ ] Test subscription update operations
- [ ] Test hard deletion (complete removal from database)
- [ ] Test user foreign key constraint enforcement
- [ ] Test labels relationship persistence
- [ ] Test unique constraint (user_id, name) enforcement

#### Complex Scenarios
- [ ] Test subscription with multiple labels
- [ ] Test user with multiple subscriptions
- [ ] Test subscription status lifecycle management
- [ ] Test payment date calculations across different time zones

### Edge Cases and Error Handling

#### Boundary Value Testing
- [ ] Test price with zero value (should be invalid)
- [ ] Test price with negative value (should be invalid)
- [ ] Test price with very large value (SQLite3 REAL type limits)
- [ ] Test price with maximum decimal precision for REAL type
- [ ] Test name with maximum allowed length
- [ ] Test name with empty string (should be invalid)
- [ ] Test notes with maximum allowed length
- [ ] Test currency code validation (USD or JPY only)

#### Invalid Data Handling
- [ ] Test creation with invalid currency code (not USD or JPY)
- [ ] Test creation with invalid payment frequency (not in constants enum)
- [ ] Test creation with invalid status (not in constants enum)
- [ ] Test creation with malformed URLs (basic format validation)
- [ ] Test creation with future dates in the past (business rule validation)
- [ ] Test creation without required user_id
- [ ] Test case-insensitive duplicate name validation per user

#### Database Constraint Testing
- [ ] Test foreign key constraint violation (invalid user_id)
- [ ] Test unique constraint handling if any
- [ ] Test null constraint violations for required fields

## Performance Considerations
- [ ] Test model creation performance with large datasets
- [ ] Test relationship loading performance (lazy vs eager loading)
- [ ] Test query performance with multiple filters

## Implementation Approach
1. Create Subscription model in `app/models/subscription.py`
2. Define SQLAlchemy table structure following `docs/db/table-definition.md`
3. Implement validation methods and business logic
4. Create relationships with User and Label models
5. Write comprehensive unit tests following this test list
6. Test database migrations and constraints

## Dependencies
- User model (existing)
- Label model (to be created)
- SQLAlchemy configuration
- Database migrations

## Estimated Effort
Medium (5-8 story points)

## Acceptance Criteria
- [ ] All model tests pass with 100% coverage
- [ ] Model follows existing code conventions and patterns
- [ ] Database schema matches table definition document
- [ ] Validation rules prevent invalid data creation
- [ ] Relationships work correctly with related models

## Design Decisions (RESOLVED)
1. **Price Storage**: ✅ Use REAL (SQLite3) for monetary values
2. **Date Handling**: ✅ Naive datetime stored as TEXT in UTC
3. **Status Enum**: ✅ Define as Python Enum in constants.py
4. **Deletion Policy**: ✅ Hard deletion (complete removal)
5. **Currency Validation**: ✅ Validate against USD and JPY only
6. **URL Validation**: ✅ Basic URL format validation

## Additional Implementation Requirements

### Database Schema (SQLite3 Specific)
- Use REAL type for price field (SQLite3 limitation)
- Store datetime as TEXT in ISO format (UTC)
- No deleted_at field needed (hard deletion)
- Add unique constraint (user_id, name) for duplicate prevention

### Currency Validation List
- Support only USD and JPY currencies
- Validate currency codes in uppercase format
- Store in constants.py for maintainability

### Payment Date Calculation
- Implement smart month-end handling logic
- Handle edge cases: Feb 29 → Feb 28, Jan 31 → Feb 28/29 → Mar 31
- Maintain end-of-month contracts as end-of-month

### Status Management
- [ ] Test status field validation (valid enum values from constants)
- [ ] Test status field accepts any valid status regardless of previous value
- [ ] Test status change is handled as simple field update
- [ ] Test status-specific business logic in service layer, not model layer
- [ ] Test status enum values from constants.py: 'trial', 'active', 'suspended', 'cancelled', 'expired'

## Implementation Status
Ready to start - all design decisions resolved
