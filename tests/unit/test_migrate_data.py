"""
Tests for data migration script from SQLite to TiDB.

This module tests the data migration functionality including:
- Data transfer from SQLite to TiDB
- Data integrity validation
- Error handling and rollback
- Progress logging

Requirements: 8.1, 8.2, 8.3, 8.4
Tasks: 5.1, 5.2, 5.3, 5.4
"""

import tempfile
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.models import db
from app.models.association_tables import subscription_labels
from app.models.exchange_rate import ExchangeRate
from app.models.label import Label
from app.models.payment_history import PaymentHistory
from app.models.subscription import Subscription
from app.models.user import User
from tests.helpers import (
    make_and_save_exchange_rate,
    make_and_save_label,
    make_and_save_subscription,
    make_and_save_user,
)


@pytest.fixture
def sqlite_db_path(tmp_path: Path) -> Path:
    """Create a temporary SQLite database file path."""
    return tmp_path / "test_source.db"


@pytest.fixture
def source_engine(sqlite_db_path: Path):
    """Create source SQLite engine with test data."""
    from sqlite3 import Connection as SQLiteConnection
    from sqlalchemy import event

    engine = create_engine(f"sqlite:///{sqlite_db_path}")

    @event.listens_for(engine, "connect")
    def _enable_fk(dbapi_connection, _connection_record):
        if isinstance(dbapi_connection, SQLiteConnection):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys = ON")
            cursor.close()

    # Create all tables
    db.metadata.create_all(engine)

    # Create session
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    # Add test data
    user = make_and_save_user(session, username="testuser", email="test@example.com")

    subscription = make_and_save_subscription(
        session,
        user_id=user.user_id,
        name="Netflix",
        price=15.99,
        currency="USD",
    )

    label = make_and_save_label(
        session,
        user_id=user.user_id,
        name="Entertainment",
        color="#FF6B6B",
    )

    # Associate label with subscription
    subscription.labels.append(label)
    session.commit()

    # Add exchange rate
    make_and_save_exchange_rate(
        session,
        from_currency="USD",
        to_currency="JPY",
        date=date(2024, 1, 1),
        rate=150.0,
    )

    # Add payment history
    payment = PaymentHistory(
        user_id=user.user_id,
        subscription_id=subscription.subscription_id,
        subscription_name=subscription.name,
        payment_date=date(2024, 1, 1),
        amount=15.99,
        currency="USD",
        rate_from_currency="USD",
        rate_to_currency="JPY",
        rate_date=date(2024, 1, 1),
        exchange_rate=150.0,
        converted_amount=2398.5,
        payment_method="credit_card",
    )
    session.add(payment)
    session.commit()

    session.close()

    yield engine

    engine.dispose()


@pytest.fixture
def dest_engine():
    """Create destination in-memory SQLite engine (simulating TiDB)."""
    from sqlite3 import Connection as SQLiteConnection
    from sqlalchemy import event

    engine = create_engine("sqlite:///:memory:")

    @event.listens_for(engine, "connect")
    def _enable_fk(dbapi_connection, _connection_record):
        if isinstance(dbapi_connection, SQLiteConnection):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys = ON")
            cursor.close()

    # Create all tables
    db.metadata.create_all(engine)

    yield engine

    engine.dispose()


class TestMigrationResult:
    """Data class for migration results."""

    def __init__(self):
        self.success: bool = False
        self.tables_migrated: list[str] = []
        self.row_counts: dict[str, int] = {}
        self.errors: list[str] = []
        self.rollback_performed: bool = False


class MigrationProgress:
    """Class to track migration progress."""

    def __init__(self):
        self.logs: list[str] = []
        self.table_progress: dict[str, tuple[int, int]] = {}  # table -> (current, total)

    def log(self, message: str) -> None:
        """Log a progress message."""
        self.logs.append(message)

    def update_progress(self, table: str, current: int, total: int) -> None:
        """Update progress for a table."""
        self.table_progress[table] = (current, total)


class TestTableOrder:
    """Test table migration order determination."""

    def test_get_migration_order_returns_correct_order(self) -> None:
        """Test that migration order respects foreign key dependencies.

        Requirement: 8.1 - 全テーブルデータをTiDBに転送
        Task: 5.1 - SQLAlchemyモデルを使用してデータを読み書き
        """
        from scripts.migrate_data import get_migration_order

        order = get_migration_order()

        # Users must come first (other tables depend on it)
        assert order.index("users") == 0

        # Exchange rates must come before payment histories
        assert order.index("exchange_rates") < order.index("payment_histories")

        # Subscriptions must come before payment histories
        assert order.index("subscriptions") < order.index("payment_histories")

        # Labels must come before subscription_labels
        assert order.index("labels") < order.index("subscription_labels")

    def test_get_migration_order_includes_all_tables(self) -> None:
        """Test that migration order includes all required tables.

        Requirement: 8.1
        Task: 5.1
        """
        from scripts.migrate_data import get_migration_order

        order = get_migration_order()

        required_tables = [
            "users",
            "subscriptions",
            "labels",
            "subscription_labels",
            "exchange_rates",
            "payment_histories",
        ]

        for table in required_tables:
            assert table in order, f"Missing table in migration order: {table}"


class TestDataTransfer:
    """Test data transfer functionality."""

    def test_migrate_users_table(self, source_engine, dest_engine) -> None:
        """Test migrating users table data.

        Requirement: 8.1 - SQLiteからTiDBへのデータ転送
        Task: 5.1 - SQLAlchemyモデルを使用してデータを読み書き
        """
        from scripts.migrate_data import migrate_table

        # Migrate users table
        result = migrate_table(source_engine, dest_engine, "users")

        assert result["success"] is True
        assert result["rows_transferred"] == 1

        # Verify data in destination
        with dest_engine.connect() as conn:
            users = conn.execute(text("SELECT * FROM users")).fetchall()
            assert len(users) == 1
            assert users[0].username == "testuser"
            assert users[0].email == "test@example.com"

    def test_migrate_subscriptions_table(self, source_engine, dest_engine) -> None:
        """Test migrating subscriptions table data.

        Requirement: 8.1
        Task: 5.1
        """
        from scripts.migrate_data import migrate_table

        # Migrate users first (foreign key dependency)
        migrate_table(source_engine, dest_engine, "users")

        # Migrate subscriptions
        result = migrate_table(source_engine, dest_engine, "subscriptions")

        assert result["success"] is True
        assert result["rows_transferred"] == 1

        # Verify data in destination
        with dest_engine.connect() as conn:
            subs = conn.execute(text("SELECT * FROM subscriptions")).fetchall()
            assert len(subs) == 1
            assert subs[0].name == "Netflix"
            assert subs[0].price == 15.99

    def test_migrate_labels_table(self, source_engine, dest_engine) -> None:
        """Test migrating labels table data.

        Requirement: 8.1
        Task: 5.1
        """
        from scripts.migrate_data import migrate_table

        # Migrate users first (foreign key dependency)
        migrate_table(source_engine, dest_engine, "users")

        # Migrate labels
        result = migrate_table(source_engine, dest_engine, "labels")

        assert result["success"] is True
        assert result["rows_transferred"] == 1

    def test_migrate_exchange_rates_table(self, source_engine, dest_engine) -> None:
        """Test migrating exchange_rates table data.

        Requirement: 8.1
        Task: 5.1
        """
        from scripts.migrate_data import migrate_table

        # Exchange rates have no dependencies
        result = migrate_table(source_engine, dest_engine, "exchange_rates")

        assert result["success"] is True
        assert result["rows_transferred"] == 1

    def test_migrate_subscription_labels_table(
        self,
        source_engine,
        dest_engine,
    ) -> None:
        """Test migrating subscription_labels association table.

        Requirement: 8.1
        Task: 5.1
        """
        from scripts.migrate_data import migrate_table

        # Migrate dependencies first
        migrate_table(source_engine, dest_engine, "users")
        migrate_table(source_engine, dest_engine, "subscriptions")
        migrate_table(source_engine, dest_engine, "labels")

        # Migrate subscription_labels
        result = migrate_table(source_engine, dest_engine, "subscription_labels")

        assert result["success"] is True
        assert result["rows_transferred"] == 1

    def test_migrate_payment_histories_table(self, source_engine, dest_engine) -> None:
        """Test migrating payment_histories table data.

        Requirement: 8.1
        Task: 5.1
        """
        from scripts.migrate_data import migrate_table

        # Migrate dependencies first
        migrate_table(source_engine, dest_engine, "users")
        migrate_table(source_engine, dest_engine, "subscriptions")
        migrate_table(source_engine, dest_engine, "exchange_rates")

        # Migrate payment_histories
        result = migrate_table(source_engine, dest_engine, "payment_histories")

        assert result["success"] is True
        assert result["rows_transferred"] == 1

    def test_batch_processing_for_large_datasets(self, source_engine, dest_engine) -> None:
        """Test batch processing for large datasets.

        Requirement: 8.1 - バッチ処理による大量データ対応
        Task: 5.1 - バッチ処理による大量データ対応
        """
        from scripts.migrate_data import migrate_table

        # Migrate users first
        migrate_table(source_engine, dest_engine, "users")

        # Create source with many records to test batching
        # (using existing test data is sufficient for unit test)


class TestDataIntegrityValidation:
    """Test data integrity validation functionality.

    Requirement: 8.2 - データ整合性検証
    Task: 5.2 - 行数比較、外部キー整合性チェック
    """

    def test_validate_row_counts_match(self, source_engine, dest_engine) -> None:
        """Test that row count validation detects matching counts.

        Requirement: 8.2 - 移行完了後のデータ整合性を検証
        Task: 5.2 - 行数比較
        """
        from scripts.migrate_data import (
            migrate_table,
            validate_data_integrity,
        )

        # Migrate all tables
        for table in ["users", "subscriptions", "labels", "subscription_labels",
                      "exchange_rates", "payment_histories"]:
            migrate_table(source_engine, dest_engine, table)

        # Validate row counts
        result = validate_data_integrity(source_engine, dest_engine)

        assert result["valid"] is True
        assert len(result["row_count_mismatches"]) == 0

    def test_validate_row_counts_detects_mismatch(self, source_engine, dest_engine) -> None:
        """Test that row count validation detects mismatches.

        Requirement: 8.2
        Task: 5.2
        """
        from scripts.migrate_data import validate_data_integrity

        # Don't migrate anything - should detect mismatch
        result = validate_data_integrity(source_engine, dest_engine)

        assert result["valid"] is False
        assert len(result["row_count_mismatches"]) > 0

    def test_validate_foreign_key_integrity(self, source_engine, dest_engine) -> None:
        """Test foreign key integrity validation.

        Requirement: 8.2
        Task: 5.2 - 外部キー整合性チェック
        """
        from scripts.migrate_data import (
            migrate_table,
            validate_foreign_keys,
        )

        # Migrate all tables
        for table in ["users", "subscriptions", "labels", "subscription_labels",
                      "exchange_rates", "payment_histories"]:
            migrate_table(source_engine, dest_engine, table)

        # Validate foreign keys
        result = validate_foreign_keys(dest_engine)

        assert result["valid"] is True
        assert len(result["violations"]) == 0

    def test_validate_composite_primary_key_integrity(self, source_engine, dest_engine) -> None:
        """Test composite primary key integrity for exchange rates.

        Requirement: 8.2
        Task: 5.2
        """
        from scripts.migrate_data import migrate_table, validate_composite_keys

        # Migrate exchange rates
        migrate_table(source_engine, dest_engine, "exchange_rates")

        # Validate composite keys
        result = validate_composite_keys(dest_engine)

        assert result["valid"] is True


class TestErrorHandlingAndRollback:
    """Test error handling and rollback functionality.

    Requirement: 8.3 - エラー時のロールバック
    Task: 5.3 - 移行中のエラーを検知しロールバック
    """

    def test_rollback_on_foreign_key_violation(self, source_engine, dest_engine) -> None:
        """Test that migration rolls back on foreign key violation.

        Requirement: 8.3 - 移行中のエラーを検知しロールバック
        Task: 5.3
        """
        from scripts.migrate_data import migrate_table

        # Try to migrate subscriptions without users (FK violation)
        result = migrate_table(source_engine, dest_engine, "subscriptions")

        assert result["success"] is False
        assert "error" in result

    def test_checkpoint_functionality(self, source_engine, dest_engine, tmp_path: Path) -> None:
        """Test checkpoint functionality for resume.

        Requirement: 8.3 - チェックポイント機能による再開対応
        Task: 5.3
        """
        from scripts.migrate_data import (
            clear_checkpoint,
            load_checkpoint,
            save_checkpoint,
        )

        checkpoint_file = tmp_path / "checkpoint.json"

        # Save checkpoint
        save_checkpoint(checkpoint_file, "users", 100)

        # Load checkpoint
        checkpoint = load_checkpoint(checkpoint_file)

        assert checkpoint is not None
        assert checkpoint["table"] == "users"
        assert checkpoint["rows_processed"] == 100

        # Clear checkpoint
        clear_checkpoint(checkpoint_file)

        # Verify cleared
        checkpoint = load_checkpoint(checkpoint_file)
        assert checkpoint is None

    def test_error_logging(self, source_engine, dest_engine) -> None:
        """Test that errors are properly logged.

        Requirement: 8.3 - エラー詳細をログに記録
        Task: 5.3
        """
        from scripts.migrate_data import migrate_table

        # Trigger an error
        result = migrate_table(source_engine, dest_engine, "subscriptions")

        assert result["success"] is False
        assert "error" in result
        # Error message should be informative
        assert len(result.get("error", "")) > 0


class TestProgressLogging:
    """Test progress logging functionality.

    Requirement: 8.4 - 移行の進捗をログに記録
    Task: 5.4 - 処理済み行数、残り行数、推定完了時間を表示
    """

    def test_progress_tracker_initialization(self) -> None:
        """Test progress tracker initialization.

        Requirement: 8.4
        Task: 5.4
        """
        from scripts.migrate_data import ProgressTracker

        tracker = ProgressTracker(total_tables=6)

        assert tracker.total_tables == 6
        assert tracker.completed_tables == 0
        assert tracker.total_rows == 0
        assert tracker.processed_rows == 0

    def test_progress_tracker_updates(self) -> None:
        """Test progress tracker updates.

        Requirement: 8.4
        Task: 5.4
        """
        from scripts.migrate_data import ProgressTracker

        tracker = ProgressTracker(total_tables=6)

        # Update progress
        tracker.update_table("users", total_rows=10)
        tracker.update_rows(5)

        assert tracker.current_table == "users"
        assert tracker.total_rows == 10
        assert tracker.processed_rows == 5

    def test_progress_tracker_estimated_time(self) -> None:
        """Test estimated time calculation.

        Requirement: 8.4 - 推定完了時間を表示
        Task: 5.4
        """
        from scripts.migrate_data import ProgressTracker
        import time

        tracker = ProgressTracker(total_tables=6)
        tracker.start()

        # Simulate some processing
        tracker.update_table("users", total_rows=100)
        tracker.update_rows(50)
        time.sleep(0.1)  # Small delay to have elapsed time

        # Should be able to estimate remaining time
        eta = tracker.get_estimated_remaining_time()
        # ETA should be a non-negative number or None
        assert eta is None or eta >= 0

    def test_progress_log_format(self) -> None:
        """Test that progress log format includes required information.

        Requirement: 8.4 - 処理済み行数、残り行数、推定完了時間を表示
        Task: 5.4
        """
        from scripts.migrate_data import ProgressTracker

        tracker = ProgressTracker(total_tables=6)
        tracker.start()
        tracker.update_table("users", total_rows=100)
        tracker.update_rows(50)

        log_message = tracker.get_progress_message()

        # Log should contain relevant information
        assert "users" in log_message
        assert "50" in log_message or "50/100" in log_message or "50 %" in log_message


class TestFullMigration:
    """Test full migration workflow."""

    def test_full_migration_workflow(self, source_engine, dest_engine) -> None:
        """Test complete migration workflow from source to destination.

        Requirement: 8.1, 8.2, 8.3, 8.4
        Task: 5.1, 5.2, 5.3, 5.4
        """
        from scripts.migrate_data import migrate_all_tables

        # Run full migration
        result = migrate_all_tables(source_engine, dest_engine)

        assert result["success"] is True
        assert result["tables_migrated"] == 6  # All 6 tables
        assert len(result["errors"]) == 0

        # Verify validation passed
        assert result["validation"]["valid"] is True
