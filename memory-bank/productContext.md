# Product Context

## Why this project exists

- Users often subscribe to multiple services and need a centralized way to track and manage them.
- Avoiding forgotten renewals and unnecessary expenses enhances financial control.

## Problems it solves

- Prevents missed payments and unexpected charges.
- Unifies subscription data from diverse services in one interface.
- Clarifies spending in different currencies with automatic conversions.

## How it works

- Backend API: Flask application exposing RESTful endpoints under `/api/v1/` using Blueprints.
- Data models: SQLAlchemy ORM mapped to SQLite for local persistence.
- Authentication: JWT-based security with `flask-jwt-extended`.
- Scheduler: APScheduler integrated to fetch and update exchange rates daily from external service.
- Notifications: In-app and email reminders triggered by scheduled jobs.

## User experience goals

- Deliver a clear dashboard of active subscriptions with totals and labels.
- Enable fast and intuitive CRUD operations for subscriptions and payments.
- Seamlessly toggle and convert between monthly and annual views and currencies.
- Ensure reliable, timely alerts to reduce cognitive load.