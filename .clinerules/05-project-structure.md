# Project Structure

The project follows a modular structure to promote separation of concerns and maintainability.

## Directory Structure

```
app/
├── api/
│   └── v1/
│       ├── auth.py
│       ├── subscription.py
│       └── settings.py
├── models/
│   ├── user.py
│   └── subscription.py
├── services/
│   ├── auth_service.py
│   └── subscription_service.py
├── schemas/
│   ├── auth.py
│   └── subscription.py
├── repositories/
│   ├── user_repository.py
│   └── subscription_repository.py
├── utils/
│   ├── validators.py
│   └── helpers.py
├── constants.py
├── config.py
└── exceptions.py
tests/
├── unit/
│   ├── models/
│   ├── services/
│   └── utils/
├── integration/
│   ├── repositories/
│   └── services/
└── api/
    └── v1/
docs/
├── openapi/             # OpenAPI specification
├── libraries/           # Generated markdown docs
├── db/                  # Database definitions
│   └── table-definition.md
├── test-list/           # Test lists for TDD
├── feature-list.md
├── MVP-proposal.md
└── system-proposal.md
migrations/              # Database migrations
.clinerules/             # Project rules and guidelines
scripts/                 # Development and utility scripts
```

## Module Responsibilities

### API Layer (`app/api/`)

- Handles HTTP requests and responses
- Defines routes and endpoints
- Validates request input
- Coordinates with services for business logic
- Formats and returns responses
- Handles authentication and authorization
- Never contains business logic directly

### Models Layer (`app/models/`)

- Defines database schema using SQLAlchemy
- Represents business entities
- Implements model-level validation
- Defines relationships between entities
- Represents the domain model structure

### Services Layer (`app/services/`)

- Implements core business logic
- Coordinates multiple repositories when needed
- Performs higher-level validation
- Manages transactions
- Never accesses database directly (uses repositories)

### Schemas Layer (`app/schemas/`)

- Defines request and response schemas using Marshmallow
- Handles data serialization and deserialization
- Implements schema-level validation
- Converts between API and domain models

### Repositories Layer (`app/repositories/`)

- Handles data access logic
- Encapsulates database queries
- Provides CRUD operations for models
- Manages entity relationships
- Abstracts database implementation details

### Utils Layer (`app/utils/`)

- Contains reusable utility functions
- Provides helper methods for common tasks
- Implements cross-cutting concerns

## File Naming Conventions

- Use snake_case for file and directory names
- Use singular nouns for model files (e.g., `user.py`, not `users.py`)
- Use plural nouns for API endpoint files (e.g., `subscriptions.py`)
- Append `_service` to service files
- Append `_repository` to repository files
- Append `_test` to test files

## Import Organization

- Group imports in the following order:
  1. Standard library imports
  2. Third-party imports
  3. Local application imports
- Sort imports alphabetically within each group
- Separate groups with a blank line

Example:

```python
# Standard library imports
import datetime
import json
import os

# Third-party imports
from flask import Blueprint, jsonify, request
from sqlalchemy import Column, String

# Local application imports
from app.constants import ErrorMessages
from app.models.user import User
from app.services.auth_service import AuthService
```

## Configuration Management

- Use environment variables for configuration
- Load environment variables from `.env` file in development
- Never hardcode configuration values
- Use `app/config.py` to centralize configuration loading
