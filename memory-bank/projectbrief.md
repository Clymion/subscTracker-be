# Project Brief

## Overview

This repository provides the backend API service for a subscription management application. It exposes RESTful endpoints for managing subscriptions, payment history, exchange rate data, and notifications.

## Objectives and Goals

- Design and implement secure REST API endpoints for subscription CRUD operations.
- Implement payment history endpoints with currency conversion support.
- Integrate daily exchange rate fetching as a background job.
- Provide JWT-based authentication and authorization for all protected routes.
- Enable a notification subsystem for payment reminders via API-triggered events.

## Scope

- API endpoints under `/api/v1/subscriptions`, `/api/v1/payments`, `/api/v1/rates`, `/api/v1/notifications`.
- Data models and persistence using SQLAlchemy and SQLite.
- Background scheduler integrated into the Flask app for rate updates.
- Error handling with standardized JSON responses.
- Docker Compose configuration for local development.

## Stakeholders

- Frontend application development team (consumes this API).
- Individual end users (via the frontend).
- DevOps/maintainers of the backend service.