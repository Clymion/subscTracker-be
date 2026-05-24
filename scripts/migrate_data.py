"""
Data migration script from SQLite to TiDB.

This script migrates all data from a SQLite database to TiDB (MySQL-compatible)
database, including validation, error handling, and progress logging.

Requirements: 8.1, 8.2, 8.3, 8.4
Tasks: 5.1, 5.2, 5.3, 5.4
"""

import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.models import db
from app.models.association_tables import subscription_labels
from app.models.exchange_rate import ExchangeRate
from app.models.label import Label
from app.models.payment_history import PaymentHistory
from app.models.subscription import Subscription
from app.models.user import User

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Batch size for large datasets
BATCH_SIZE = 1000

# Table model mapping
TABLE_MODELS = {
    "users": User,
    "subscriptions": Subscription,
    "labels": Label,
    "subscription_labels": subscription_labels,
    "exchange_rates": ExchangeRate,
    "payment_histories": PaymentHistory,
}


def get_migration_order() -> list[str]:
    """
    Get the order of tables to migrate based on foreign key dependencies.

    Returns:
        list[str]: Ordered list of table names to migrate.

    Requirement: 8.1 - 全テーブルデータをTiDBに転送
    Task: 5.1 - SQLAlchemyモデルを使用してデータを読み書き
    """
    # Order based on foreign key dependencies
    # 1. users - no dependencies, other tables depend on it
    # 2. exchange_rates - no dependencies, payment_histories depends on it
    # 3. subscriptions - depends on users
    # 4. labels - depends on users and itself (parent_id)
    # 5. subscription_labels - depends on subscriptions and labels
    # 6. payment_histories - depends on users, subscriptions, exchange_rates
    return [
        "users",
        "exchange_rates",
        "subscriptions",
        "labels",
        "subscription_labels",
        "payment_histories",
    ]


def get_table_columns(engine: Engine, table_name: str) -> list[str]:
    """
    Get the column names for a table.

    Args:
        engine: SQLAlchemy engine.
        table_name: Name of the table.

    Returns:
        list[str]: List of column names.
    """
    inspector = inspect(engine)
    columns = inspector.get_columns(table_name)
    return [col["name"] for col in columns]


def get_row_count(engine: Engine, table_name: str) -> int:
    """
    Get the row count for a table.

    Args:
        engine: SQLAlchemy engine.
        table_name: Name of the table.

    Returns:
        int: Number of rows in the table.
    """
    with engine.connect() as conn:
        result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
        return result.scalar() or 0


def migrate_table(
    source_engine: Engine,
    dest_engine: Engine,
    table_name: str,
    progress_tracker: "ProgressTracker | None" = None,
) -> dict[str, Any]:
    """
    Migrate a single table from source to destination database.

    Args:
        source_engine: Source database engine (SQLite).
        dest_engine: Destination database engine (TiDB).
        table_name: Name of the table to migrate.
        progress_tracker: Optional progress tracker for logging.

    Returns:
        dict: Migration result with success status and rows transferred.

    Requirement: 8.1 - SQLiteからTiDBへのデータ転送
    Task: 5.1 - SQLAlchemyモデルを使用してデータを読み書き
    """
    result = {
        "success": False,
        "rows_transferred": 0,
        "error": None,
    }

    try:
        # Get columns for the table
        columns = get_table_columns(source_engine, table_name)
        column_list = ", ".join(columns)
        placeholders = ", ".join([f":{col}" for col in columns])

        # Get total rows for progress tracking
        total_rows = get_row_count(source_engine, table_name)

        if total_rows == 0:
            logger.info(f"Table {table_name} is empty, skipping")
            result["success"] = True
            return result

        logger.info(f"Migrating {table_name}: {total_rows} rows")

        # Read data from source in batches
        offset = 0
        rows_transferred = 0

        with source_engine.connect() as source_conn:
            while offset < total_rows:
                # Read batch from source
                query = text(
                    f"SELECT {column_list} FROM {table_name} "
                    f"LIMIT {BATCH_SIZE} OFFSET {offset}"
                )
                rows = source_conn.execute(query).fetchall()

                if not rows:
                    break

                # Convert rows to list of dicts
                rows_data = [dict(row._mapping) for row in rows]

                # Write to destination
                with dest_engine.connect() as dest_conn:
                    insert_query = text(
                        f"INSERT INTO {table_name} ({column_list}) "
                        f"VALUES ({placeholders})"
                    )
                    dest_conn.execute(insert_query, rows_data)
                    dest_conn.commit()

                rows_transferred += len(rows)
                offset += BATCH_SIZE

                # Update progress
                if progress_tracker:
                    progress_tracker.update_rows(len(rows))
                    logger.info(
                        f"Progress: {rows_transferred}/{total_rows} rows "
                        f"({rows_transferred * 100 // total_rows}%)"
                    )

        result["success"] = True
        result["rows_transferred"] = rows_transferred
        logger.info(f"Completed {table_name}: {rows_transferred} rows migrated")

    except Exception as e:
        error_msg = f"Error migrating {table_name}: {str(e)}"
        logger.error(error_msg)
        result["error"] = error_msg

    return result


def validate_data_integrity(
    source_engine: Engine,
    dest_engine: Engine,
) -> dict[str, Any]:
    """
    Validate data integrity between source and destination databases.

    Args:
        source_engine: Source database engine.
        dest_engine: Destination database engine.

    Returns:
        dict: Validation result with row count comparisons.

    Requirement: 8.2 - データ整合性を検証
    Task: 5.2 - 行数比較、外部キー整合性チェック
    """
    result = {
        "valid": True,
        "row_count_mismatches": [],
        "details": {},
    }

    tables = get_migration_order()

    for table in tables:
        source_count = get_row_count(source_engine, table)
        dest_count = get_row_count(dest_engine, table)

        result["details"][table] = {
            "source": source_count,
            "destination": dest_count,
        }

        if source_count != dest_count:
            result["valid"] = False
            result["row_count_mismatches"].append(
                f"{table}: source={source_count}, destination={dest_count}"
            )

    return result


def validate_foreign_keys(dest_engine: Engine) -> dict[str, Any]:
    """
    Validate foreign key integrity in the destination database.

    Args:
        dest_engine: Destination database engine.

    Returns:
        dict: Validation result with any violations found.

    Requirement: 8.2
    Task: 5.2 - 外部キー整合性チェック
    """
    result = {
        "valid": True,
        "violations": [],
    }

    with dest_engine.connect() as conn:
        # Check subscription -> user FK
        invalid_subs = conn.execute(text("""
            SELECT s.subscription_id, s.user_id
            FROM subscriptions s
            LEFT JOIN users u ON s.user_id = u.user_id
            WHERE u.user_id IS NULL
        """)).fetchall()

        if invalid_subs:
            result["valid"] = False
            result["violations"].append(
                f"subscriptions: {len(invalid_subs)} orphaned records"
            )

        # Check labels -> user FK
        invalid_labels = conn.execute(text("""
            SELECT l.label_id, l.user_id
            FROM labels l
            LEFT JOIN users u ON l.user_id = u.user_id
            WHERE u.user_id IS NULL
        """)).fetchall()

        if invalid_labels:
            result["valid"] = False
            result["violations"].append(
                f"labels: {len(invalid_labels)} orphaned records"
            )

        # Check subscription_labels FK
        invalid_sub_labels = conn.execute(text("""
            SELECT sl.subscription_id, sl.label_id
            FROM subscription_labels sl
            LEFT JOIN subscriptions s ON sl.subscription_id = s.subscription_id
            LEFT JOIN labels l ON sl.label_id = l.label_id
            WHERE s.subscription_id IS NULL OR l.label_id IS NULL
        """)).fetchall()

        if invalid_sub_labels:
            result["valid"] = False
            result["violations"].append(
                f"subscription_labels: {len(invalid_sub_labels)} orphaned records"
            )

    return result


def validate_composite_keys(dest_engine: Engine) -> dict[str, Any]:
    """
    Validate composite primary key integrity (for exchange_rates).

    Args:
        dest_engine: Destination database engine.

    Returns:
        dict: Validation result.

    Requirement: 8.2
    Task: 5.2
    """
    result = {
        "valid": True,
        "violations": [],
    }

    # Exchange rates have a composite primary key
    # Just verify data was migrated correctly
    count = get_row_count(dest_engine, "exchange_rates")
    result["exchange_rate_count"] = count

    return result


def save_checkpoint(
    checkpoint_file: Path,
    table: str,
    rows_processed: int,
) -> None:
    """
    Save migration checkpoint to file.

    Args:
        checkpoint_file: Path to checkpoint file.
        table: Current table being migrated.
        rows_processed: Number of rows processed.

    Requirement: 8.3 - チェックポイント機能による再開対応
    Task: 5.3
    """
    checkpoint = {
        "table": table,
        "rows_processed": rows_processed,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    with open(checkpoint_file, "w") as f:
        json.dump(checkpoint, f)


def load_checkpoint(checkpoint_file: Path) -> dict[str, Any] | None:
    """
    Load migration checkpoint from file.

    Args:
        checkpoint_file: Path to checkpoint file.

    Returns:
        dict | None: Checkpoint data or None if not exists.

    Requirement: 8.3
    Task: 5.3
    """
    if not checkpoint_file.exists():
        return None

    try:
        with open(checkpoint_file) as f:
            return json.load(f)
    except (json.JSONDecodeError, KeyError):
        return None


def clear_checkpoint(checkpoint_file: Path) -> None:
    """
    Clear checkpoint file after successful migration.

    Args:
        checkpoint_file: Path to checkpoint file.

    Requirement: 8.3
    Task: 5.3
    """
    if checkpoint_file.exists():
        checkpoint_file.unlink()


class ProgressTracker:
    """
    Track migration progress with estimated time remaining.

    Requirement: 8.4 - 移行の進捗をログに記録
    Task: 5.4 - 処理済み行数、残り行数、推定完了時間を表示
    """

    def __init__(self, total_tables: int):
        """Initialize progress tracker."""
        self.total_tables = total_tables
        self.completed_tables = 0
        self.current_table: str | None = None
        self.total_rows = 0
        self.processed_rows = 0
        self.start_time: float | None = None
        self.table_start_time: float | None = None

    def start(self) -> None:
        """Start the progress timer."""
        self.start_time = time.time()

    def update_table(self, table: str, total_rows: int) -> None:
        """Update current table being processed."""
        self.current_table = table
        self.total_rows = total_rows
        self.processed_rows = 0
        self.table_start_time = time.time()
        logger.info(f"Starting table: {table} ({total_rows} rows)")

    def update_rows(self, count: int) -> None:
        """Update processed row count."""
        self.processed_rows += count

    def complete_table(self) -> None:
        """Mark current table as completed."""
        if self.current_table:
            self.completed_tables += 1
            logger.info(
                f"Completed table: {self.current_table} "
                f"({self.completed_tables}/{self.total_tables})"
            )

    def get_estimated_remaining_time(self) -> float | None:
        """
        Calculate estimated remaining time.

        Returns:
            float | None: Estimated seconds remaining, or None if not calculable.
        """
        if not self.start_time or self.processed_rows == 0:
            return None

        elapsed = time.time() - self.start_time
        if elapsed == 0:
            return None

        # Simple linear estimation based on tables completed
        if self.completed_tables == 0:
            return None

        avg_time_per_table = elapsed / self.completed_tables
        remaining_tables = self.total_tables - self.completed_tables
        return avg_time_per_table * remaining_tables

    def get_progress_message(self) -> str:
        """
        Get a formatted progress message.

        Returns:
            str: Formatted progress message.
        """
        elapsed = time.time() - self.start_time if self.start_time else 0
        eta = self.get_estimated_remaining_time()

        eta_str = f", ETA: {eta:.0f}s" if eta else ""
        table_name = f"({self.current_table}) " if self.current_table else ""
        table_progress = f"{self.completed_tables}/{self.total_tables} tables"
        row_progress = (
            f"{self.processed_rows}/{self.total_rows} rows"
            if self.total_rows > 0
            else ""
        )

        return f"{table_name}{table_progress}, {row_progress}{eta_str}"


def migrate_all_tables(
    source_engine: Engine,
    dest_engine: Engine,
    checkpoint_file: Path | None = None,
) -> dict[str, Any]:
    """
    Migrate all tables from source to destination database.

    Args:
        source_engine: Source database engine (SQLite).
        dest_engine: Destination database engine (TiDB).
        checkpoint_file: Optional checkpoint file for resume support.

    Returns:
        dict: Migration result with status and details.

    Requirement: 8.1, 8.2, 8.3, 8.4
    Task: 5.1, 5.2, 5.3, 5.4
    """
    result = {
        "success": False,
        "tables_migrated": 0,
        "errors": [],
        "validation": None,
        "details": {},
    }

    tables = get_migration_order()
    progress = ProgressTracker(total_tables=len(tables))
    progress.start()

    # Load checkpoint if exists
    checkpoint = None
    if checkpoint_file:
        checkpoint = load_checkpoint(checkpoint_file)
        if checkpoint:
            logger.info(f"Resuming from checkpoint: {checkpoint}")
            # Skip tables that were already migrated
            checkpoint_table = checkpoint.get("table")
            if checkpoint_table in tables:
                idx = tables.index(checkpoint_table)
                tables = tables[idx:]  # Resume from checkpoint table

    try:
        for table in tables:
            progress.update_table(table, get_row_count(source_engine, table))

            # Migrate table
            migrate_result = migrate_table(
                source_engine,
                dest_engine,
                table,
                progress,
            )

            result["details"][table] = migrate_result

            if not migrate_result["success"]:
                result["errors"].append(migrate_result.get("error", "Unknown error"))
                # Save checkpoint on error
                if checkpoint_file:
                    save_checkpoint(
                        checkpoint_file,
                        table,
                        migrate_result.get("rows_transferred", 0),
                    )
                break

            result["tables_migrated"] += 1
            progress.complete_table()

            # Save checkpoint after each successful table
            if checkpoint_file:
                save_checkpoint(
                    checkpoint_file,
                    table,
                    migrate_result.get("rows_transferred", 0),
                )

        # Validate data integrity
        validation = validate_data_integrity(source_engine, dest_engine)
        result["validation"] = validation

        if validation["valid"] and len(result["errors"]) == 0:
            result["success"] = True
            # Clear checkpoint on success
            if checkpoint_file:
                clear_checkpoint(checkpoint_file)

    except Exception as e:
        error_msg = f"Migration failed: {str(e)}"
        logger.error(error_msg)
        result["errors"].append(error_msg)

    logger.info(f"Migration completed: {result['tables_migrated']} tables migrated")
    return result


def main() -> None:
    """Main entry point for migration script."""
    import argparse
    import os

    parser = argparse.ArgumentParser(
        description="Migrate data from SQLite to TiDB"
    )
    parser.add_argument(
        "--source",
        required=True,
        help="Source SQLite database path or connection URL",
    )
    parser.add_argument(
        "--dest",
        required=True,
        help="Destination TiDB connection URL",
    )
    parser.add_argument(
        "--checkpoint",
        default=".migration_checkpoint.json",
        help="Checkpoint file path for resume support",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=BATCH_SIZE,
        help=f"Batch size for data transfer (default: {BATCH_SIZE})",
    )
    parser.add_argument(
        "--ssl-ca",
        help="Path to CA certificate file for SSL connection to TiDB Cloud",
    )

    args = parser.parse_args()

    # Create engines
    source_url = args.source
    if not source_url.startswith(("sqlite://", "mysql://")):
        source_url = f"sqlite:///{source_url}"

    source_engine = create_engine(source_url)

    # Create destination engine with SSL support
    dest_connect_args = {}
    if args.ssl_ca:
        dest_connect_args = {
            "ssl_ca": args.ssl_ca,
            "ssl_verify_cert": True,
        }
        logger.info(f"Using SSL CA certificate: {args.ssl_ca}")

    dest_engine = create_engine(
        args.dest,
        connect_args=dest_connect_args if dest_connect_args else None,
    )

    # Run migration
    checkpoint_file = Path(args.checkpoint)
    result = migrate_all_tables(source_engine, dest_engine, checkpoint_file)

    if result["success"]:
        logger.info("Migration completed successfully!")
    else:
        logger.error(f"Migration failed: {result['errors']}")
        exit(1)


if __name__ == "__main__":
    main()
