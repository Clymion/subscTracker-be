# Project Structure

This document describes the directory structure, code organization patterns, and naming conventions for the project.

## Root Directory Organization

- **`app/`**: Contains the core application source code.
- **`tests/`**: Holds all unit and integration tests.
- **`migrations/`**: Stores Alembic database migration scripts.
- **`docs/`**: Contains project documentation, including OpenAPI specs and database diagrams.
- **`.kiro/`**: Stores steering and specification files for AI-driven development.
- **`scripts/`**: Utility and maintenance scripts.
- **`docker/`**: Docker-related files, including the `Dockerfile`.
- **`pyproject.toml`**: Defines project dependencies and tool configurations for Poetry.
- **`compose.yml`**: Docker Compose file for orchestrating the development environment.

## Subdirectory Structures

### `app/` Directory

- **`api/v1/`**: Defines the API endpoints (routes). Each file corresponds to a resource (e.g., `auth.py`, `subscription.py`).
- **`models/`**: Contains SQLAlchemy ORM models, defining the database schema.
- **`services/`**: Implements the business logic. Services are called by the API layer and interact with repositories.
- **`repositories/`**: Handles direct database operations (CRUD). It abstracts the data access logic from the services.
- **`common/`**: Includes shared utilities like authentication middleware, error handlers, and logging setup.
- **`config.py`**: Manages application configuration using Pydantic.
- **`constants.py`**: Stores application-wide constants.

### `tests/` Directory

- **`unit/`**: Unit tests for individual components (e.g., services, models) in isolation.
- **`integration/`**: Integration tests that verify the interaction between different components (e.g., API endpoints and the database).
- **`fixtures/`**: Pytest fixtures for setting up test data and environments.
- **`conftest.py`**: Global test configurations and fixtures for Pytest.

## Code Organization Patterns

- **Layered Architecture**: The code is organized into distinct layers (API, Service, Repository) to separate concerns.
- **Dependency Injection**: Configuration and database sessions are injected into different parts of the application, promoting loose coupling.
- **Blueprint-based Routing**: Flask Blueprints are used in `app/api/v1/` to modularize API routes.

## File Naming Conventions

- **Python files**: `snake_case.py` (e.g., `subscription_service.py`).
- **Test files**: `test_*.py` (e.g., `test_subscription_api.py`).
- **API resource files**: Named after the resource they manage (e.g., `label.py`).

## Import Organization

- Imports are grouped into three sections: standard library, third-party packages, and local application modules.
- Absolute imports from the project root (`app.`) are preferred to maintain clarity.
