"""
Tests for database migration and constraint validation.

This module tests that database indexes and constraints are properly
created and functioning as expected.
"""

from collections.abc import Generator
from datetime import date

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models.label import Label
from app.models.subscription import Subscription
from tests.helpers import make_and_save_user


@pytest.mark.integration
class TestDatabaseMigration:
    """Test database migration functionality."""

    def test_subscription_composite_indexes_exist(
        self,
        clean_db: Generator[Session, None, None],
    ):
        """Test that composite indexes for subscriptions are created."""
        # Act: Query SQLite master table for indexes
        index_query = text(
            """
            SELECT name FROM sqlite_master
            WHERE type='index' AND name LIKE 'idx_subscriptions_%'
        """,
        )

        indexes = {row[0] for row in clean_db.execute(index_query).fetchall()}

        # Assert: Required composite indexes should exist
        required_indexes = {
            "idx_subscriptions_user_status",
            "idx_subscriptions_pagination",
            "idx_subscriptions_pagination_name",
            "idx_subscriptions_pagination_price",
        }

        for index_name in required_indexes:
            assert index_name in indexes, f"Missing required index: {index_name}"

    def test_label_composite_indexes_exist(
        self,
        clean_db: Generator[Session, None, None],
    ):
        """Test that composite indexes for labels are created."""
        # Act: Query SQLite master table for indexes
        index_query = text(
            """
            SELECT name FROM sqlite_master
            WHERE type='index' AND name LIKE 'idx_labels_%'
        """,
        )

        indexes = {row[0] for row in clean_db.execute(index_query).fetchall()}

        # Assert: Required composite indexes should exist
        required_indexes = {"idx_labels_user_parent"}

        for index_name in required_indexes:
            assert index_name in indexes, f"Missing required index: {index_name}"

    def test_foreign_key_constraints_enabled(
        self,
        clean_db: Generator[Session, None, None],
    ):
        """Test that foreign key constraints are enabled in SQLite."""
        # Act: Check if foreign keys are enabled
        result = clean_db.execute(text("PRAGMA foreign_keys")).fetchone()

        # Assert: Foreign keys should be enabled
        assert result is not None
        assert bool(result[0]) is True, "Foreign key constraints are not enabled"

    def test_subscription_user_foreign_key_constraint(
        self,
        clean_db: Generator[Session, None, None],
    ):
        """Test that subscription-user foreign key constraint works."""
        # Arrange: Create user and subscription
        user = make_and_save_user(clean_db)
        subscription = Subscription(
            user_id=user.user_id,
            name="Test Subscription",
            price=9.99,
            currency="USD",
            initial_payment_date=date(2024, 1, 1),
            next_payment_date=date(2024, 2, 1),
            payment_frequency="monthly",
            payment_method="credit_card",
            status="active",
        )
        clean_db.add(subscription)
        clean_db.commit()

        # Act: Delete user (should cascade delete subscription)
        clean_db.delete(user)
        clean_db.commit()

        # Assert: Subscription should be automatically deleted
        remaining_subscriptions = (
            clean_db.query(Subscription).filter_by(user_id=user.user_id).count()
        )
        assert remaining_subscriptions == 0

    def test_label_user_foreign_key_constraint(
        self,
        clean_db: Generator[Session, None, None],
    ):
        """Test that label-user foreign key constraint works."""
        # Arrange: Create user and label
        user = make_and_save_user(clean_db)
        label = Label(user_id=user.user_id, name="Test Label", color="#FF6B6B")
        clean_db.add(label)
        clean_db.commit()

        # Act: Delete user (should cascade delete label)
        clean_db.delete(user)
        clean_db.commit()

        # Assert: Label should be automatically deleted
        remaining_labels = clean_db.query(Label).filter_by(user_id=user.user_id).count()
        assert remaining_labels == 0

    def test_label_parent_child_foreign_key_constraint(
        self,
        clean_db: Generator[Session, None, None],
    ):
        """Test that label parent-child foreign key constraint works."""
        # Arrange: Create user, parent label, and child label
        user = make_and_save_user(clean_db)

        parent_label = Label(user_id=user.user_id, name="Parent Label", color="#FF0000")
        clean_db.add(parent_label)
        clean_db.flush()

        child_label = Label(
            user_id=user.user_id,
            parent_id=parent_label.label_id,
            name="Child Label",
            color="#00FF00",
        )
        clean_db.add(child_label)
        clean_db.commit()

        # Act: Delete parent label (should cascade delete child)
        clean_db.delete(parent_label)
        clean_db.commit()

        # Assert: Child label should be automatically deleted
        remaining_children = (
            clean_db.query(Label).filter_by(parent_id=parent_label.label_id).count()
        )
        assert remaining_children == 0

    def test_subscription_labels_foreign_key_constraints(
        self,
        clean_db: Generator[Session, None, None],
    ):
        """Test that subscription-labels association table constraints work."""
        # Arrange: Create user, subscription, and label
        user = make_and_save_user(clean_db)

        subscription = Subscription(
            user_id=user.user_id,
            name="Test Subscription",
            price=9.99,
            currency="USD",
            initial_payment_date=date(2024, 1, 1),
            next_payment_date=date(2024, 2, 1),
            payment_frequency="monthly",
            payment_method="credit_card",
            status="active",
        )
        clean_db.add(subscription)

        label = Label(user_id=user.user_id, name="Test Label", color="#FF6B6B")
        clean_db.add(label)
        clean_db.flush()

        # Create association
        subscription.labels.append(label)
        clean_db.commit()

        # Verify association exists
        assert len(subscription.labels) == 1
        assert subscription.labels[0] == label

        # Act: Delete subscription (should remove association)
        clean_db.delete(subscription)
        clean_db.commit()

        # Assert: Label should still exist but association should be removed
        remaining_label = (
            clean_db.query(Label).filter_by(label_id=label.label_id).first()
        )
        assert remaining_label is not None
        assert len(remaining_label.subscriptions) == 0


@pytest.mark.integration
class TestDatabasePerformance:
    """Test database performance with indexes."""

    def test_subscription_user_status_index_performance(
        self,
        clean_db: Generator[Session, None, None],
    ):
        """Test that user+status queries use the composite index."""
        # Arrange: Create test data
        user = make_and_save_user(clean_db)

        # Create multiple subscriptions with different statuses
        statuses = ["active", "trial", "cancelled", "suspended", "expired"]
        for i, status in enumerate(statuses * 5):  # 25 subscriptions total
            subscription = Subscription(
                user_id=user.user_id,
                name=f"Subscription {i}",
                price=9.99 + i,
                currency="USD",
                initial_payment_date=date(2024, 1, 1),
                next_payment_date=date(2024, 2, 1),
                payment_frequency="monthly",
                payment_method="credit_card",
                status=status,
            )
            clean_db.add(subscription)
        clean_db.commit()

        # Act: Query with user_id and status (should use composite index)
        active_subscriptions = (
            clean_db.query(Subscription)
            .filter_by(user_id=user.user_id, status="active")
            .all()
        )

        # Assert: Should find correct number of active subscriptions
        assert len(active_subscriptions) == 5

        # Verify index usage by checking query plan
        explain_query = text(
            """
            EXPLAIN QUERY PLAN
            SELECT * FROM subscriptions
            WHERE user_id = :user_id AND status = :status
        """,
        )

        plan = clean_db.execute(
            explain_query,
            {"user_id": user.user_id, "status": "active"},
        ).fetchall()

        # Check that the query plan mentions index usage
        plan_text = " ".join(str(row) for row in plan)
        assert "idx_subscriptions_user_status" in plan_text

    def test_label_user_parent_index_performance(
        self,
        clean_db: Generator[Session, None, None],
    ):
        """Test that user+parent queries use the composite index."""
        # Arrange: Create test data
        user = make_and_save_user(clean_db)

        # Create parent label
        parent_label = Label(user_id=user.user_id, name="Parent Label", color="#FF0000")
        clean_db.add(parent_label)
        clean_db.flush()

        # Create multiple child labels
        for i in range(10):
            child_label = Label(
                user_id=user.user_id,
                parent_id=parent_label.label_id,
                name=f"Child Label {i}",
                color=f"#{i:02d}FF{i:02d}",
            )
            clean_db.add(child_label)
        clean_db.commit()

        # Act: Query with user_id and parent_id (should use composite index)
        child_labels = (
            clean_db.query(Label)
            .filter_by(user_id=user.user_id, parent_id=parent_label.label_id)
            .all()
        )

        # Assert: Should find all child labels
        assert len(child_labels) == 10

        # Verify index usage by checking query plan
        explain_query = text(
            """
            EXPLAIN QUERY PLAN
            SELECT * FROM labels
            WHERE user_id = :user_id AND parent_id = :parent_id
        """,
        )

        plan = clean_db.execute(
            explain_query,
            {"user_id": user.user_id, "parent_id": parent_label.label_id},
        ).fetchall()

        # Check that the query plan mentions index usage
        plan_text = " ".join(str(row) for row in plan)
        assert "idx_labels_user_parent" in plan_text


@pytest.mark.integration
class TestSchemaIntegrity:
    """Test database schema integrity."""

    def test_all_required_tables_exist(
        self,
        clean_db: Generator[Session, None, None],
    ):
        """Test that all required tables are created."""
        # Act: Query for table existence
        tables_query = text(
            """
            SELECT name FROM sqlite_master
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
        """,
        )

        tables = {row[0] for row in clean_db.execute(tables_query).fetchall()}

        # Assert: All required tables should exist
        required_tables = {"users", "subscriptions", "labels", "subscription_labels"}

        for table_name in required_tables:
            assert table_name in tables, f"Missing required table: {table_name}"

    def test_table_schemas_match_models(
        self,
        clean_db: Generator[Session, None, None],
    ):
        """Test that table schemas match model definitions."""
        # This test verifies that SQLAlchemy models match actual database schema

        # Test subscription table schema
        subscription_schema = clean_db.execute(
            text("PRAGMA table_info(subscriptions)"),
        ).fetchall()

        subscription_columns = {row[1] for row in subscription_schema}
        required_subscription_columns = {
            "subscription_id",
            "user_id",
            "name",
            "price",
            "currency",
            "initial_payment_date",
            "next_payment_date",
            "payment_frequency",
            "payment_method",
            "status",
            "url",
            "notes",
            "image_url",
            "created_at",
            "updated_at",
        }

        assert required_subscription_columns.issubset(subscription_columns)

        # Test label table schema
        label_schema = clean_db.execute(text("PRAGMA table_info(labels)")).fetchall()

        label_columns = {row[1] for row in label_schema}
        required_label_columns = {
            "label_id",
            "user_id",
            "parent_id",
            "name",
            "color",
            "system_label",
            "created_at",
            "updated_at",
        }

        assert required_label_columns.issubset(label_columns)
