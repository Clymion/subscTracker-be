# Test List: Label Management System

## Feature Description
Complete label management system including model, service, and API for organizing subscriptions with user-defined labels and hierarchical structure.

## Related Requirements
- REQ-LABEL-001: Users can create custom labels for organizing subscriptions
- REQ-LABEL-002: Labels have name and color properties
- REQ-LABEL-003: Labels are user-specific (isolated per user)
- REQ-LABEL-004: Labels can be assigned to multiple subscriptions
- REQ-LABEL-005: Labels track usage count for UI display
- REQ-LABEL-006: Labels support hierarchical structure (parent-child relationships)
- REQ-LABEL-007: System default labels cannot be deleted

## Test Categories

### Unit Tests - Label Model

#### Model Creation and Validation
- [ ] Test Label creation with all required fields
- [ ] Test Label creation with minimal required fields
- [ ] Test default values are applied correctly
- [ ] Test model attributes are correctly assigned
- [ ] Test string representation returns expected format

#### Field Validation
- [ ] Test name field validation (required, max length, not empty)
- [ ] Test color field validation (required, valid hex color format #FFFFFF)
- [ ] Test color normalization (#fff → #FFFFFF, lowercase → uppercase)
- [ ] Test user_id field validation (required, foreign key)
- [ ] Test parent_id field validation (optional, self-referential foreign key)
- [ ] Test hierarchy depth validation (maximum 5 levels)
- [ ] Test name uniqueness per user and parent (case-insensitive)
- [ ] Test system_label flag (cannot be deleted if true)

#### Relationship Validation
- [ ] Test subscriptions relationship (many-to-many)
- [ ] Test adding subscriptions to label
- [ ] Test removing subscriptions from label

#### Relationship Validation (Model-Level Only)
- [ ] Test user relationship (foreign key constraint)
- [ ] Test user relationship returns correct User object
- [ ] Test parent-child relationship (self-referential)
- [ ] Test children collection returns direct children only
- [ ] Test ancestors traversal up the hierarchy
- [ ] Test descendants traversal down the hierarchy

#### Business Logic Methods (Without Subscription Dependencies)
- [ ] Test can_be_deleted() based on system_label flag only
- [ ] Test color validation accepts valid hex colors (#FFFFFF, #FFF)
- [ ] Test color validation rejects invalid formats
- [ ] Test get_full_path() returns hierarchical path (Parent > Child > Grandchild)
- [ ] Test get_ancestors() returns all parent labels
- [ ] Test get_descendants() returns all child labels
- [ ] Test get_depth() returns hierarchy level (0 for root)
- [ ] Test is_ancestor_of() checks parent-child relationships
- [ ] Test prevent_circular_reference() validation

#### Business Logic Methods (Mock Subscription Dependencies)
- [ ] Test calculate_usage_count() method exists and returns integer
- [ ] Test is_used() method exists and returns boolean
- [ ] Test usage calculation logic with mocked subscription relationships
- [ ] Test can_be_deleted() considers both system_label and usage (with mocked usage)

### Unit Tests - Label Service

#### LabelService Setup
- [ ] Test LabelService initialization with database session
- [ ] Test LabelService initialization with repository dependency
- [ ] Test service instance creation is successful

#### Create Label (create_label)
- [ ] Test create_label with valid data creates label
- [ ] Test create_label sets correct user_id
- [ ] Test create_label with duplicate name raises error (case-insensitive, per parent)
- [ ] Test create_label validates color format and normalizes (#fff → #FFFFFF)
- [ ] Test create_label with invalid user_id raises error
- [ ] Test create_label initializes system_label to false by default
- [ ] Test create_label with parent_id creates nested label
- [ ] Test create_label prevents circular references
- [ ] Test create_label validates maximum hierarchy depth (5 levels)

#### Get Label (get_label)
- [ ] Test get_label returns correct label by ID
- [ ] Test get_label raises error for non-existent ID
- [ ] Test get_label validates user ownership
- [ ] Test get_label denies access to other user's label
- [ ] Test get_label includes usage count

#### Get Labels List (get_labels_by_user)
- [ ] Test get_labels_by_user returns all user labels
- [ ] Test get_labels_by_user returns empty list for user with no labels
- [ ] Test get_labels_by_user sorts by hierarchy then name by default
- [ ] Test get_labels_by_user sorts by usage count (real-time calculation)
- [ ] Test get_labels_by_user excludes other users' labels
- [ ] Test get_labels_by_user includes usage statistics (real-time)
- [ ] Test get_labels_by_user returns hierarchical structure
- [ ] Test get_labels_by_user includes system default labels
- [ ] Test get_labels_by_user filters by parent_id for tree navigation

#### Update Label (update_label)
- [ ] Test update_label updates fields correctly
- [ ] Test update_label validates user ownership
- [ ] Test update_label prevents duplicate names (case-insensitive, per parent)
- [ ] Test update_label validates color format and normalizes
- [ ] Test update_label raises error for non-existent label
- [ ] Test update_label denies access to other user's label
- [ ] Test update_label prevents system_label modification
- [ ] Test update_label handles parent_id changes with validation
- [ ] Test update_label prevents circular references when changing parent
- [ ] Test update_label validates hierarchy depth when moving labels

#### Delete Label (delete_label)
- [ ] Test delete_label performs hard deletion (complete removal with cascade)
- [ ] Test delete_label validates user ownership
- [ ] Test delete_label handles labels with subscriptions (cascade removal)
- [ ] Test delete_label raises error for non-existent label
- [ ] Test delete_label denies access to other user's label
- [ ] Test delete_label prevents deletion of system default labels
- [ ] Test delete_label handles child labels (cascade deletion)
- [ ] Test delete_label updates subscription relationships

#### Usage Management
- [ ] Test calculate_usage_counts() real-time calculation for all labels
- [ ] Test get_most_used_labels() returns correct ordering
- [ ] Test get_unused_labels() returns labels with zero usage
- [ ] Test usage count accuracy after subscription operations
- [ ] Test hierarchical usage count (includes child label usage)
- [ ] Test performance of real-time usage calculation

### Unit Tests - Label API

#### GET /api/v1/labels
- [ ] Test route handler calls service with correct parameters
- [ ] Test route handler formats response correctly
- [ ] Test route handler handles service exceptions
- [ ] Test route handler includes usage statistics

#### POST /api/v1/labels
- [ ] Test route handler validates request JSON
- [ ] Test route handler calls service with correct data
- [ ] Test route handler returns 201 on successful creation
- [ ] Test route handler handles validation errors

#### PUT /api/v1/labels/{id}
- [ ] Test route handler validates request JSON
- [ ] Test route handler calls service with correct data
- [ ] Test route handler returns updated label
- [ ] Test route handler handles validation errors

#### DELETE /api/v1/labels/{id}
- [ ] Test route handler calls service with correct ID
- [ ] Test route handler returns 204 on successful deletion
- [ ] Test route handler handles labels in use

### Integration Tests - Label API

#### Authentication and Authorization
- [ ] Test all endpoints require valid JWT token
- [ ] Test endpoints reject expired/invalid tokens
- [ ] Test users can only access their own labels
- [ ] Test users cannot access other users' labels

#### GET /api/v1/labels - List Labels
- [ ] Test returns 200 and list of user's labels
- [ ] Test returns empty array for user with no labels
- [ ] Test response includes usage count for each label (real-time)
- [ ] Test response sorts labels hierarchically
- [ ] Test response format matches OpenAPI specification
- [ ] Test response includes system default labels
- [ ] Test response shows hierarchical structure with nested levels
- [ ] Test pagination if large number of labels

#### POST /api/v1/labels - Create Label
- [ ] Test creates label with valid data returns 201
- [ ] Test created label belongs to authenticated user
- [ ] Test duplicate name for same user and parent returns 400 (case-insensitive)
- [ ] Test missing required fields returns 400
- [ ] Test invalid color format returns 400
- [ ] Test very long name returns 400
- [ ] Test color normalization (#fff → #FFFFFF)
- [ ] Test nested label creation with parent_id
- [ ] Test maximum hierarchy depth validation (5 levels)
- [ ] Test circular reference prevention

#### PUT /api/v1/labels/{id} - Update Label
- [ ] Test updates label with valid data returns 200
- [ ] Test updated label reflects changes
- [ ] Test duplicate name validation works (case-insensitive, per parent)
- [ ] Test returns 404 for non-existent label
- [ ] Test returns 403 when updating other user's label
- [ ] Test invalid field values return 400
- [ ] Test prevents modification of system default labels
- [ ] Test parent_id changes with hierarchy validation
- [ ] Test circular reference prevention during updates
- [ ] Test color normalization during updates

#### DELETE /api/v1/labels/{id} - Delete Label
- [ ] Test deletes label returns 204 (hard deletion with cascade)
- [ ] Test label is actually removed from database
- [ ] Test returns 404 for non-existent label
- [ ] Test returns 403 when deleting other user's label
- [ ] Test handles labels with subscriptions (cascade removal)
- [ ] Test prevents deletion of system default labels
- [ ] Test cascade deletion of child labels
- [ ] Test subscription relationship cleanup

### Integration Tests - Label-Subscription Relationship

#### Label Assignment
- [ ] Test assigning labels to subscription works correctly
- [ ] Test removing labels from subscription works correctly
- [ ] Test subscription can have multiple labels (including hierarchical)
- [ ] Test label can be assigned to multiple subscriptions
- [ ] Test label usage count updates when assigned/removed (real-time calculation)
- [ ] Test hierarchical label assignment (parent and child on same subscription)
- [ ] Test label inheritance in hierarchy if needed

#### Cascade Operations
- [ ] Test deleting subscription updates label usage counts (real-time)
- [ ] Test deleting label removes subscription relationships (hard deletion)
- [ ] Test label statistics remain accurate after operations
- [ ] Test deleting parent label cascades to child labels
- [ ] Test hard deletion compatibility with subscription system

### Data Validation Tests

#### Label Name Validation
- [ ] Test name cannot be empty string
- [ ] Test name cannot be only whitespace
- [ ] Test name maximum length enforcement
- [ ] Test name with special characters
- [ ] Test name with unicode characters
- [ ] Test name case-insensitive uniqueness (per user per parent)
- [ ] Test name uniqueness across different parents (allowed)
- [ ] Test name normalization for comparison

#### Color Format Validation
- [ ] Test valid hex color formats (#FFFFFF, #FFF)
- [ ] Test invalid hex color formats (missing #, wrong length, invalid characters)
- [ ] Test color value normalization (lowercase → uppercase, #FFF → #FFFFFF)
- [ ] Test predefined color constants if supported
- [ ] Test color accessibility considerations (contrast ratios)
- [ ] Test color duplicate detection if needed

#### Business Rule Validation
- [ ] Test label name uniqueness per user per parent (case-insensitive)
- [ ] Test label name can be same across different users
- [ ] Test label name can be same under different parents
- [ ] Test usage count accuracy after multiple operations (real-time calculation)
- [ ] Test system default labels cannot be deleted or modified
- [ ] Test maximum hierarchy depth (5 levels) enforcement
- [ ] Test circular reference prevention in hierarchy

### Error Handling Tests

#### Service Layer Errors
- [ ] Test service handles database connection errors
- [ ] Test service handles constraint violation errors
- [ ] Test service provides meaningful error messages
- [ ] Test service validates user permissions consistently

#### API Layer Errors
- [ ] Test validation errors return 400 with detailed messages
- [ ] Test authentication errors return 401
- [ ] Test authorization errors return 403
- [ ] Test not found errors return 404
- [ ] Test error responses follow standard format

### Performance Tests
- [ ] Test label creation performance
- [ ] Test label listing performance with many labels
- [ ] Test usage count calculation performance
- [ ] Test concurrent label operations

### Edge Cases and Boundary Testing

#### Boundary Values
- [ ] Test label name at maximum length
- [ ] Test label with maximum usage count (real-time calculation)
- [ ] Test user with maximum hierarchy depth (5 levels)
- [ ] Test color edge cases (pure black #000000, pure white #FFFFFF)
- [ ] Test maximum number of children per parent label
- [ ] Test performance with deep hierarchy traversal

#### Concurrent Access
- [ ] Test multiple users creating labels simultaneously
- [ ] Test concurrent updates to same label
- [ ] Test race conditions in usage count updates (real-time calculation)
- [ ] Test race conditions in hierarchy modifications
- [ ] Test concurrent subscription-label assignments

### Integration with Subscription System

#### Label-Subscription Workflow
- [ ] Test complete workflow: create label → assign to subscription → verify usage
- [ ] Test removing subscription updates label usage correctly
- [ ] Test filtering subscriptions by label works correctly
- [ ] Test subscription API includes label information

#### Data Consistency
- [ ] Test label usage counts remain accurate across operations (real-time)
- [ ] Test orphaned relationships are cleaned up properly (hard deletion)
- [ ] Test database integrity constraints are enforced
- [ ] Test hierarchy integrity after operations (no circular references)
- [ ] Test system default labels are maintained correctly

## Implementation Approach
1. Create Label model in `app/models/label.py`
2. Create SubscriptionLabel association table for many-to-many relationship
3. Create LabelService in `app/services/label_service.py`
4. Create LabelRepository in `app/repositories/label_repository.py`
5. Create label API endpoints in `app/api/v1/labels.py`
6. Write comprehensive tests following this test list
7. Test integration with existing subscription system

## Dependencies
- User model (existing)
- Subscription model (from subscription test list)
- Database session management
- Authentication system integration

## Estimated Effort
Medium-Large (6-10 story points)

## Acceptance Criteria
- [ ] All label tests pass with 90%+ coverage
- [ ] Label system integrates seamlessly with subscriptions
- [ ] Label API follows existing patterns and conventions
- [ ] Usage counts are accurate and performant
- [ ] User isolation is properly enforced
- [ ] Error handling is comprehensive and user-friendly

## Design Decisions (RESOLVED)
1. **Color Storage**: ✅ Store as hex strings (#FFFFFF format)
2. **Usage Tracking**: ✅ Real-time calculation (no stored counters)
3. **Label Hierarchy**: ✅ Nested categories (max 5 levels deep)
4. **Deletion Policy**: ✅ Hard deletion with cascade
5. **Name Constraints**: ✅ Case-insensitive uniqueness per user per parent
6. **Default Labels**: ✅ Provide system default labels
7. **Label Limits**: ✅ Unlimited labels per user

## Additional Implementation Requirements

### Nested Category Structure
- Support up to 5 levels of nesting (parent → child → grandchild...)
- Use self-referential foreign key (parent_id)
- Implement tree traversal methods for hierarchy display

### System Default Labels
- Provide common categories: Entertainment, Productivity, Education, Health, etc.
- Auto-create for new users
- Cannot be deleted (system_label flag = true)

### Color Validation
- Validate hex color format (#FFFFFF or #FFF)
- Normalize to uppercase 6-character format
- Provide default color palette for user selection

### Usage Calculation
- Real-time count via subscription relationships
- No stored usage_count field
- Efficient query for displaying usage statistics

### Hierarchy Management
- Prevent circular references
- Enforce maximum depth (5 levels)
- Cascade deletion for parent-child relationships
- Validate parent changes to prevent orphaning

## Implementation Status
Ready to start - all design decisions resolved
