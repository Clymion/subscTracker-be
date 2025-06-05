# Test List: Subscription API Endpoints

## Feature Description
RESTful API endpoints for subscription management with authentication, authorization, and CRUD operations.

## Related Requirements
- REQ-API-001: All endpoints require JWT authentication
- REQ-API-002: Users can only access their own subscriptions
- REQ-API-003: Provide standard REST operations (GET, POST, PUT, DELETE)
- REQ-API-004: Support filtering, sorting, and pagination
- REQ-API-005: Return standardized JSON responses

## Test Categories

### Unit Tests - Route Handlers

#### GET /api/v1/subscriptions
- [ ] Test route handler calls service with correct parameters
- [ ] Test route handler handles pagination parameters
- [ ] Test route handler handles filter parameters
- [ ] Test route handler handles sort parameters
- [ ] Test route handler formats response correctly
- [ ] Test route handler handles service exceptions

#### POST /api/v1/subscriptions
- [ ] Test route handler validates request JSON
- [ ] Test route handler calls service with correct data
- [ ] Test route handler returns 201 on successful creation
- [ ] Test route handler includes created subscription in response
- [ ] Test route handler handles validation errors
- [ ] Test route handler handles duplicate name errors

#### GET /api/v1/subscriptions/{id}
- [ ] Test route handler calls service with correct subscription ID
- [ ] Test route handler returns subscription details
- [ ] Test route handler handles non-existent subscription
- [ ] Test route handler handles unauthorized access

#### PUT /api/v1/subscriptions/{id}
- [ ] Test route handler validates request JSON
- [ ] Test route handler calls service with correct data
- [ ] Test route handler returns updated subscription
- [ ] Test route handler handles partial updates
- [ ] Test route handler handles validation errors
- [ ] Test route handler handles unauthorized access

#### DELETE /api/v1/subscriptions/{id}
- [ ] Test route handler calls service with correct ID
- [ ] Test route handler returns 204 on successful deletion
- [ ] Test route handler handles non-existent subscription
- [ ] Test route handler handles unauthorized access

### Integration Tests - API Endpoints

#### Authentication and Authorization
- [ ] Test all endpoints require valid JWT token
- [ ] Test endpoints reject expired tokens
- [ ] Test endpoints reject malformed tokens
- [ ] Test endpoints reject missing Authorization header
- [ ] Test users can only access their own subscriptions
- [ ] Test users cannot access other users' subscriptions

#### GET /api/v1/subscriptions - List Subscriptions
- [ ] Test returns 200 and list of user's subscriptions (full objects)
- [ ] Test returns empty array for user with no subscriptions
- [ ] Test pagination works (limit/offset parameters)
- [ ] Test filtering by status works
- [ ] Test filtering by currency works (USD or JPY only)
- [ ] Test filtering by labels works
- [ ] Test filtering by price range works
- [ ] Test sorting by name (asc/desc) works
- [ ] Test sorting by price (asc/desc) works
- [ ] Test sorting by next_payment_date works
- [ ] Test response includes pagination metadata
- [ ] Test response includes summary information (total count, total cost)

#### POST /api/v1/subscriptions - Create Subscription
- [ ] Test creates subscription with valid data returns 201
- [ ] Test created subscription includes all provided fields (full object)
- [ ] Test created subscription belongs to authenticated user
- [ ] Test next_payment_date is calculated correctly with smart month-end handling
- [ ] Test duplicate name for same user returns 400 (case-insensitive)
- [ ] Test missing required fields returns 400
- [ ] Test invalid price (negative/zero) returns 400
- [ ] Test invalid currency code returns 400 (not USD or JPY)
- [ ] Test invalid payment_frequency returns 400 (not in constants enum)
- [ ] Test invalid status returns 400 (not in constants enum)
- [ ] Test any valid status can be set during creation
- [ ] Test invalid URL format returns 400
- [ ] Test labels are assigned correctly
- [ ] Test price stored as REAL type compatible value

#### GET /api/v1/subscriptions/{id} - Get Subscription Details
- [ ] Test returns 200 and subscription details for valid ID
- [ ] Test returns 404 for non-existent subscription ID
- [ ] Test returns 403 when accessing other user's subscription
- [ ] Test response includes all subscription fields
- [ ] Test response includes related labels
- [ ] Test response format matches OpenAPI specification

#### PUT /api/v1/subscriptions/{id} - Update Subscription
- [ ] Test updates subscription with valid data returns 200
- [ ] Test updated subscription reflects changes (full object response)
- [ ] Test partial updates work correctly (PUT semantics with full replacement)
- [ ] Test next_payment_date recalculated when frequency changes (smart month-end)
- [ ] Test duplicate name validation works (case-insensitive, per-user)
- [ ] Test returns 404 for non-existent subscription
- [ ] Test returns 403 when updating other user's subscription
- [ ] Test invalid field values return 400
- [ ] Test any valid status can be set (user-driven, no transition rules)
- [ ] Test status can be changed from any status to any valid status
- [ ] Test labels can be updated
- [ ] Test currency code validation (USD or JPY only, uppercase normalization)

#### DELETE /api/v1/subscriptions/{id} - Delete Subscription
- [ ] Test deletes subscription returns 204 (hard deletion)
- [ ] Test subscription is completely removed from database
- [ ] Test returns 404 for non-existent subscription
- [ ] Test returns 403 when deleting other user's subscription
- [ ] Test handles related data appropriately (cascade label relationships)

### API Response Format Tests

#### Success Response Format
- [ ] Test all successful responses follow standard format (data/meta structure)
- [ ] Test list endpoints include pagination metadata
- [ ] Test single resource endpoints include resource data (full objects)
- [ ] Test created resources return complete object data
- [ ] Test updated resources return updated object data

#### Error Response Format
- [ ] Test validation errors return 400 with detailed messages
- [ ] Test authentication errors return 401 with appropriate message
- [ ] Test authorization errors return 403 with appropriate message
- [ ] Test not found errors return 404 with appropriate message
- [ ] Test all error responses follow standard error format
- [ ] Test error messages use centralized constants
- [ ] Test custom exceptions are properly handled (SubscriptionError, DuplicateSubscriptionError)

### Data Validation Tests

#### Request Body Validation
- [ ] Test required fields validation
- [ ] Test field type validation (string, number, boolean)
- [ ] Test field length validation (max string lengths)
- [ ] Test field format validation (email, URL, currency codes)
- [ ] Test nested object validation (labels)
- [ ] Test array validation (label arrays)
- [ ] Test price validation (positive REAL type values)
- [ ] Test currency code validation (USD or JPY only)
- [ ] Test status enum validation (constants.py values, no transition rules)
- [ ] Test status field accepts any valid enum value regardless of current status

#### Query Parameter Validation
- [ ] Test pagination parameter validation (limit, offset - offset/limit strategy)
- [ ] Test filter parameter validation
- [ ] Test sort parameter validation
- [ ] Test invalid parameter values return appropriate errors
- [ ] Test parameter type coercion (string to int for pagination)

### Content Type and Headers Tests
- [ ] Test endpoints accept application/json content type
- [ ] Test endpoints reject invalid content types
- [ ] Test endpoints return application/json responses
- [ ] Test CORS headers if required
- [ ] Test rate limiting headers if implemented

### Edge Cases and Error Scenarios

#### Boundary Value Testing
- [ ] Test maximum allowed values for numeric fields (REAL type limits)
- [ ] Test minimum allowed values for numeric fields
- [ ] Test maximum string lengths
- [ ] Test empty string handling
- [ ] Test null value handling in optional fields
- [ ] Test currency code edge cases (case normalization)

#### Concurrent Access Testing
- [ ] Test multiple users creating subscriptions simultaneously
- [ ] Test concurrent updates to same subscription (optimistic locking)
- [ ] Test race conditions in duplicate name validation (case-insensitive)
- [ ] Test service-level transaction isolation

#### Large Dataset Testing
- [ ] Test performance with large number of subscriptions per user
- [ ] Test pagination with large datasets (offset/limit strategy)
- [ ] Test filtering performance with large datasets
- [ ] Test sorting performance with large datasets
- [ ] Test full object response performance (decided: no summary objects)

### Integration with Existing Systems

#### Authentication Integration
- [ ] Test API works with existing JWT authentication
- [ ] Test API integrates with auth middleware properly
- [ ] Test API uses current user context correctly

#### Database Integration
- [ ] Test API handles database connection errors
- [ ] Test API handles database timeout errors
- [ ] Test API maintains transaction integrity

#### Error Handling Integration
- [ ] Test API uses existing error handlers
- [ ] Test API error responses match existing format
- [ ] Test API logs errors appropriately

## Performance Tests
- [ ] Test response times under normal load
- [ ] Test response times with large datasets
- [ ] Test concurrent request handling
- [ ] Test memory usage with large responses

## Security Tests
- [ ] Test SQL injection prevention
- [ ] Test XSS prevention in responses
- [ ] Test input sanitization
- [ ] Test sensitive data not exposed in errors
- [ ] Test proper HTTPS handling

## Implementation Approach
1. Create subscription blueprint in `app/api/v1/subscriptions.py`
2. Follow existing auth blueprint patterns and conventions
3. Implement all CRUD endpoints with proper error handling
4. Apply authentication middleware to all endpoints
5. Write comprehensive API tests following this test list
6. Test integration with existing systems

## Dependencies
- Subscription service (from previous test list)
- Existing authentication middleware
- Common response utilities
- Error handling system

## Estimated Effort
Large (8-13 story points)

## Acceptance Criteria
- [ ] All API tests pass with 90%+ coverage
- [ ] API follows RESTful conventions
- [ ] API integrates properly with existing authentication
- [ ] API responses follow standardized format
- [ ] API handles all error cases gracefully
- [ ] API performance meets requirements

## Design Decisions (RESOLVED)
1. **URL Structure**: ✅ Flat structure `/subscriptions` 
2. **Pagination**: ✅ Offset/limit pagination
3. **Response Format**: ✅ Full objects in list endpoints
4. **Partial Updates**: ✅ PUT semantics for updates
5. **Error Handling**: ✅ Custom exceptions with standardized responses
6. **Authentication**: ✅ JWT middleware integration
7. **Deletion Policy**: ✅ Hard deletion (complete removal)

## Additional Implementation Requirements

### URL Structure
- Use flat `/api/v1/subscriptions` structure
- User context from JWT authentication
- RESTful resource-centric design

### Response Format
- Full objects in list endpoints (decided: not summary objects)
- Consistent error response format using existing error handlers
- Standard pagination metadata format

### Authentication Integration
- Leverage existing jwt_required_custom middleware
- Use get_jwt_identity() for user context
- Maintain existing authorization patterns

### Currency Support
- Support only USD and JPY currencies
- Validate currency codes in uppercase format
- Store currency validation rules in constants.py

## Implementation Status
Ready to start - all design decisions resolved
