# Technology Stack

This document outlines the technology stack, architecture, and development environment for the subscription management backend API.

## Architecture

- **System Design**: The application is a monolithic backend API built with Flask. It follows a standard three-tier architecture (API layer, Service layer, Repository layer).
- **Database**: It primarily uses SQLite for both development and production, simplifying setup and maintenance. For testing, an in-memory SQLite database is utilized.
- **Replication & Backup**: Litestream is used for real-time replication and backup of the SQLite database to a cloud storage provider, ensuring data durability.
- **Containerization**: The entire application is containerized using Docker, with separate stages for building and production to create a lightweight final image.

## Backend

- **Language**: Python 3.13
- **Framework**: Flask 3.1.0
- **Data Access**: SQLAlchemy 2.x is used as the ORM for database interactions, along with Alembic for managing database migrations.
- **Authentication**: JWTs (JSON Web Tokens) are implemented for securing API endpoints via the `flask-jwt-extended` library.
- **Configuration**: Application settings are managed using `pydantic-settings` (version 2.9.1), which loads configuration from environment variables and `.env` files.
- **API Specification**: OpenAPI (Swagger) specifications are maintained in `docs/openapi/` and served via the application.
- **Other Key Libraries**: `pydantic` (2.11.4), `python-dotenv` (1.1.0), `marshmallow` (4.0.0), `flask-sqlalchemy` (3.1.1), `gunicorn` (23.0.0), `flask-swagger-ui` (5.21.0), `prance` (25.4.8.0), `openapi-spec-validator` (0.7.2), `psutil` (7.0.0), `flask-cors` (6.0.1), `google-cloud-secret-manager` (2.24.0).

## Development Environment

- **Dependency Management**: Project dependencies are managed by Poetry.
- **Local Setup**: The development environment is orchestrated using Docker Compose, which runs the backend API service.
- **Code Quality**: Code formatting and linting are enforced using Black (24.10.0) and Ruff (0.8.4).
- **Testing**: The testing framework is `pytest` (7.0.0), used for both unit and integration tests, with `pytest-cov` for coverage reporting.

## Common Commands

- **Start Development Server**: `docker-compose up --build`
- **Run All Tests**: `poetry run pytest`
- **Apply Database Migrations**: `./scripts/apply_migrations.sh`
- **Run Linter/Formatter**: `ruff check .` and `black .`
- **Fetch Exchange Rates**: `./scripts/fetch_exchange_rates.sh` or `poetry run python scripts/fetch_exchange_rates.py`

## Environment Variables

Key environment variables are defined in `app/config.py` and loaded from a `.env` file. 

- `DB_DRIVER`: Database driver (e.g., `sqlite`, `mysql`, `postgres`). Default: `sqlite`.
- `DB_HOST`: Database host. Default: `localhost`.
- `DB_PORT`: Database port. Default: `5432`.
- `DB_NAME`: Database name/path. Default: `instance/app.db`.
- `DB_USER`: Database user. Default: `postgres`.
- `DB_PASSWORD`: Database password (optional).
- `API_PORT`: Port for the API server. Default: `5000`.
- `DEBUG`: Enables or disables debug mode. Default: `False`.
- `JWT_SECRET_KEY`: Secret key for signing JWTs (required, min 16 chars).
- `JWT_ACCESS_TOKEN_EXPIRES`: JWT access token expiration in seconds. Default: `3600`.
- `JWT_REFRESH_TOKEN_EXPIRES`: JWT refresh token expiration in seconds. Default: `2592000`.
- `ALLOWED_ORIGINS`: Comma-separated list of URLs for CORS. Default: `["https://subsctracker-fe.web.app"]`.
- `ENABLE_NEW_BILLING`: Feature flag for new billing. Default: `False`.

## Port Configuration

- **Development**: The API server runs on port `5000` locally (as configured in `compose.yml`).
- **Production (Cloud Run)**: The container listens on port `8080`, as specified by the `PORT` environment variable in the `Dockerfile`.
