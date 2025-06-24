"""
Subscription Repository for data access.

This module provides a repository class for abstracting data access logic
for the Subscription model, separating business logic from data persistence.
"""

from typing import Any

from sqlalchemy import asc, desc
from sqlalchemy.orm import Session

from app.models.label import Label
from app.models.subscription import Subscription


class SubscriptionRepository:
    """Repository for subscription data access logic."""

    def __init__(self, session: Session) -> None:
        """
        Initialize the repository with a database session.

        Args:
            session: The SQLAlchemy Session object.
        """
        self.session = session

    def find_by_id(self, subscription_id: int) -> Subscription | None:
        """Find a subscription by its ID."""
        return (
            self.session.query(Subscription)
            .filter_by(subscription_id=subscription_id)
            .first()
        )

    def find_by_user_and_name(self, user_id: int, name: str) -> Subscription | None:
        """Find a subscription by user ID and name (case-insensitive)."""
        return (
            self.session.query(Subscription)
            .filter(Subscription.user_id == user_id, Subscription.name.ilike(name))
            .first()
        )

    def find_all_by_user_id(
        self,
        user_id: int,
        filters: dict[str, Any],
        sort_by: str | None,  # Noneを許容するように型ヒントを修正
        sort_order: str,
        limit: int,
        offset: int,
    ) -> list[Subscription]:
        """Find all subscriptions for a user with filtering, sorting, and pagination."""
        query = self.session.query(Subscription).filter(Subscription.user_id == user_id)

        # Apply filters
        if "status" in filters:
            query = query.filter(Subscription.status.in_(filters["status"]))
        if "currency" in filters:
            query = query.filter(Subscription.currency == filters["currency"])
        if "label_ids" in filters:
            query = query.join(Subscription.labels).filter(
                Label.label_id.in_(filters["label_ids"]),
            )

        # Apply sorting
        sort_key = sort_by or "created_at"
        sort_column = getattr(Subscription, sort_key, Subscription.created_at)

        if sort_order == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(asc(sort_column))

        # Apply pagination
        return query.limit(limit).offset(offset).all()

    def count_all_by_user_id(self, user_id: int, filters: dict[str, Any]) -> int:
        """Count all subscriptions for a user with filtering."""
        query = self.session.query(Subscription.subscription_id).filter(
            Subscription.user_id == user_id,
        )

        # Apply filters
        if "status" in filters:
            query = query.filter(Subscription.status.in_(filters["status"]))
        if "currency" in filters:
            query = query.filter(Subscription.currency == filters["currency"])
        if "label_ids" in filters:
            query = query.join(Subscription.labels).filter(
                Label.label_id.in_(filters["label_ids"]),
            )

        return query.count()

    def save(self, subscription: Subscription) -> Subscription:
        """Save a subscription (create or update)."""
        self.session.add(subscription)
        self.session.commit()
        self.session.refresh(subscription)
        return subscription

    def delete(self, subscription: Subscription) -> None:
        """Delete a subscription."""
        self.session.delete(subscription)
        self.session.commit()
