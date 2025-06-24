"""
Association tables for many-to-many relationships.

This module defines intermediate tables for many-to-many relationships
between different models in the application.
"""

from sqlalchemy import Column, ForeignKey, Integer, Table

from app.models import db

# Subscription-Label Many-to-Many relationship table
subscription_labels = Table(
    "subscription_labels",
    db.metadata,
    Column(
        "subscription_id",
        Integer,
        ForeignKey("subscriptions.subscription_id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "label_id",
        Integer,
        ForeignKey("labels.label_id", ondelete="CASCADE"),
        primary_key=True,
    ),
)
