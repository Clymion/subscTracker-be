# System Patterns

## System architecture

- Backend API service built with Flask, served in a Docker container.
- SQLite database accessed via SQLAlchemy within the API service container.
- APScheduler integrated into the Flask app for daily exchange rate retrieval.
- Notification subsystem runs as part of the API, emitting in-app and email reminders.

## Key technical decisions

- React and Material UI for a responsive, component-driven UI.
- Flask Blueprint structure for modular API endpoints.
- JWT authentication using flask-jwt-extended for secure routes.
- SQLite for lightweight, zero-ops data storage.
- Docker Compose to containerize frontend, backend, and scheduler.

## Design patterns in use

- RESTful API endpoints organized by resource blueprints.
- Repository/Service layer abstraction for database operations.
- Scheduler pattern for periodic tasks (exchange rate updates).
- Observer pattern for dispatching notifications on state changes.

## Component relationships

- API Clients ↔ API: REST HTTP requests and JSON responses.
- API ↔ Database: SQLAlchemy ORM sessions manage persistence in SQLite.
- API ↔ External FX service: HTTP client module fetches rates daily.
- API Scheduler (APScheduler) ↔ API core: invokes exchange rate update routines within app.
- API core ↔ Notification subsystem: triggers reminder jobs and dispatches notifications.