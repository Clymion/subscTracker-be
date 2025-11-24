# Product Overview

This project is the backend API for a web application designed to help individual users efficiently manage their personal subscription services. It provides a centralized platform to track expenses, manage renewals, and gain a clear overview of all active subscriptions.

## Core Features

- **User Authentication**: Secure user registration and login using JWT-based authentication, including access/refresh tokens and secure password hashing.
- **Subscription Management**: Full CRUD (Create, Read, Update, Delete) functionality for subscription services, including labeling and status management (e.g., trial, paused).
- **Payment History Management**: Supports registration and editing of payment records, multi-currency handling, and automatic exchange rate fetching.
- **Exchange Rate Automation**: Automatically fetches and updates exchange rates daily to provide accurate cost conversions for foreign currency subscriptions.
- **Notification System**: Sends reminders for upcoming payment deadlines via email/push notifications to prevent missed payments.
- **Spending Analysis**: Offers reporting and visualization features to help users understand their spending habits (monthly/annual summaries).
- **Common Infrastructure**: Standardized API response format, pagination, comprehensive error handling, structured logging, and environment configuration management (pydantic-settings).
- **Testing Infrastructure**: Comprehensive unit and integration tests (90%+ coverage), test data factories, and CI/CD readiness.

## Target Use Case

The application is designed for individuals who:
- Subscribe to multiple services (e.g., streaming, software, news) and struggle to keep track of them.
- Want to accurately monitor their monthly and annual subscription-related expenditures.
- Need to manage subscriptions in different currencies and want a unified view in their native currency.
- Wish to avoid unexpected renewal charges and have better control over their finances.

## Key Value Proposition

- **Centralized Control**: Unifies all subscription information into a single, easy-to-manage dashboard.
- **Financial Clarity**: Provides a clear and accurate overview of all subscription-related spending, with automatic currency conversion.
- **Cost Prevention**: Helps users avoid unwanted renewal charges and identify unnecessary subscriptions through timely reminders and clear data presentation.
- **Simplified Management**: Streamlines the process of adding, updating, and removing subscriptions, saving users time and effort.
