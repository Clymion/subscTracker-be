# Technical Context

## Technologies used

- Backend framework: Flask 3.1.0
- Programming language: Python 3.13
- Authentication: flask-jwt-extended
- ORM: SQLAlchemy 2.x
- Scheduling: APScheduler for daily exchange rate updates
- Data storage: SQLite
- Environment management: python-dotenv
- Serialization/Validation: Marshmallow, Pydantic
- Containerization: Docker, Docker Compose
- Dependency management: Poetry
- Testing: pytest, pytest-cov
- Linting/Formatting: Black, Ruff

## Development setup

- Clone the repository and run `docker-compose up --build` to start the backend API.
- Configure environment variables in a `.env` file (`FLASK_APP`, `FLASK_ENV`, `FLASK_DEBUG`, etc).
- Backend API listens on port 5000(Possible changes), exposing endpoints under `/api/v1/`.
- Local SQLite database file persists within the workspace volume.
- Poetry manages Python dependencies inside the container.

## Technical constraints

- Single-developer project with limited time and resources.
- Lightweight, zero-ops database using SQLite to avoid external DB servers.
- Integrated scheduler (APScheduler) instead of external cron jobs.
- No external message broker; notifications handled within the API service.

## Dependencies

- flask = "^3.1.0"
- flask-jwt-extended = "^4.7.1"
- sqlalchemy = "^2.0.40"
- apscheduler = "^3.x"
- python-dotenv = "^1.1.0"
- marshmallow = "^4.0.0"
- pydantic = "^2.11.4"
- black = "^24.10.0"
- ruff = "^0.8.4"
- pytest = "^7.0.0"
- pytest-cov = "^4.0.0"