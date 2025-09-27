# Technology Stack

This document outlines the technology stack, architecture, and development environment for the subscription management backend API.

## Architecture

- **System Design**: The application is a monolithic backend API built with Flask. It follows a standard three-tier architecture (API layer, Service layer, Repository layer).
- **Database**: It uses SQLite as its primary database for both development and production, simplifying setup and maintenance. 
- **Replication & Backup**: Litestream is used for real-time replication and backup of the SQLite database to a cloud storage provider, ensuring data durability.
- **Containerization**: The entire application is containerized using Docker, with separate stages for building and production to create a lightweight final image.

## Backend

- **Language**: Python 3.13
- **Framework**: Flask 3.1.0
- **Data Access**: SQLAlchemy 2.x is used as the ORM for database interactions, along with Alembic for managing database migrations.
- **Authentication**: JWTs (JSON Web Tokens) are implemented for securing API endpoints via the `flask-jwt-extended` library.
- **Configuration**: Application settings are managed using `pydantic-settings`, which loads configuration from environment variables and `.env` files.
- **API Specification**: OpenAPI (Swagger) specifications are maintained in `docs/openapi/` and served via the application.

## Development Environment

- **Dependency Management**: Project dependencies are managed by Poetry.
- **Local Setup**: The development environment is orchestrated using Docker Compose, which runs the backend API service.
- **Code Quality**: Code formatting and linting are enforced using Black and Ruff.
- **Testing**: The testing framework is `pytest`, used for both unit and integration tests.

## Common Commands

- **Start Development Server**: `docker-compose up --build`
- **Run All Tests**: `poetry run pytest`
- **Apply Database Migrations**: `./scripts/apply_migrations.sh`
- **Run Linter/Formatter**: `ruff check .` and `black .`

## Environment Variables

Key environment variables are defined in `app/config.py` and loaded from a `.env` file. 

- `DB_NAME`: Path to the SQLite database file (e.g., `instance/app.db`).
- `JWT_SECRET_KEY`: Secret key for signing JWTs (required).
- `ALLOWED_ORIGINS`: Comma-separated list of URLs for CORS.
- `API_PORT`: Port for the API server (defaults to `5000`).
- `DEBUG`: Enables or disables debug mode.

## Port Configuration

- **Development**: The API server runs on port `5000` locally.
- **Production (Cloud Run)**: The container listens on port `8080`, as specified by the `PORT` environment variable.
