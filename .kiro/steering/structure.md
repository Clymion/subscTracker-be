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
- **`.env.example`**: Example environment variables file.
- **`.gitignore`**: Specifies intentionally untracked files to ignore.
- **`README.md`**: Main project README file.
- **`ruff.toml`**: Configuration for the Ruff linter/formatter.

## Subdirectory Structures

### `app/` Directory

- **`api/v1/`**: Defines the API endpoints (routes). Each file corresponds to a resource (e.g., `auth.py`, `subscription.py`, `exchange_rate.py`, `label.py`, `payment_history.py`, `system.py`, `swagger.py`).
- **`models/`**: Contains SQLAlchemy ORM models, defining the database schema (e.g., `user.py`, `subscription.py`, `label.py`, `exchange_rate.py`, `payment_history.py`, `association_tables.py`).
- **`services/`**: Implements the business logic. Services are called by the API layer and interact with repositories (e.g., `auth_service.py`, `subscription_service.py`, `exchange_rate_service.py`, `label_service.py`, `payment_history_service.py`).
- **`repositories/`**: Handles direct database operations (CRUD). It abstracts the data access logic from the services (e.g., `exchange_rate_repository.py`, `label_repository.py`, `payment_history_repository.py`, `subscription_repository.py`).
- **`common/`**: Includes shared utilities like authentication middleware (`auth_middleware.py`), error handlers (`error_handlers.py`), logging setup (`logging_setup.py`), and response utilities (`response_utils.py`).
- **`config.py`**: Manages application configuration using Pydantic.
- **`constants.py`**: Stores application-wide constants.
- **`exceptions.py`**: Defines custom application exceptions.

### `tests/` Directory

- **`unit/`**: Unit tests for individual components (e.g., `test_auth_service.py`, `test_exchange_rate_service.py`, `test_payment_history_service.py`, `test_subscription_service.py`, `test_config.py`, `test_api_response_common.py`, `test_auth_middleware.py`, `test_label_model.py`, `test_user_model.py`).
- **`integration/`**: Integration tests that verify the interaction between different components (e.g., `test_auth_api.py`, `test_exchange_rate_api.py`, `test_label_api.py`, `test_payment_history_api.py`, `test_subscription_api.py`, `test_migration.py`).
- **`fixtures/`**: Pytest fixtures for setting up test data and environments (e.g., `config.py`).
- **`conftest.py`**: Global test configurations and fixtures for Pytest.
- **`helpers.py`**: Helper functions for tests.

### `docs/` Directory

- **`openapi/`**: Contains OpenAPI specification files (`openapi.yaml`), with subdirectories for `components/` and `paths/`, and a `build/` directory for bundled specs.
- **`db/`**: Database design documentation (`ER-diagram.md`, `table-definition.md`).
- **`test-list/`**: TDD test lists for various features (e.g., `authentication.md`, `exchange-rate.md`, `label.md`, `subscription-api.md`).
- **`MVP-proposal.md`**: MVP proposal document.
- **`feature-list.md`**: List of features.
- **`system-proposal.md`**: System proposal document.
- **`action-flowchart.md`**: Action flowchart.
- **`screen-flow-diagram.md`**: Screen flow diagram.

### `scripts/` Directory

- **`apply_migrations.sh`**: Script to apply database migrations.
- **`fetch_exchange_rates.py`**: Python script to fetch exchange rates.
- **`fetch_exchange_rates.sh`**: Shell script to run the exchange rate fetching Python script.
- **`dev/`**: Development-related scripts (e.g., `pull_prd_sqlite.sh`).

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
