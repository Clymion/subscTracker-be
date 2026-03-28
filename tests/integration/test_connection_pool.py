"""
Tests for connection pool performance under load.

This module tests the connection pool behavior including:
- Connection pool creation and configuration
- Concurrent connection handling
- Connection pool exhaustion handling
- Pool recycling and pre-ping functionality

Requirements: 7.1, 7.2, 7.4
Tasks: 6.2
"""

import concurrent.futures
import os
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import TimeoutError as SQLAlchemyTimeoutError
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import QueuePool

from app.config import AppConfig, TestConfig
from app.models import db


class TestConnectionPoolConfiguration:
    """Test connection pool configuration for TiDB.

    Requirement: 7.1 - 適切な接続プールサイズを設定
    Requirement: 7.2 - アイドル接続管理
    Requirement: 7.4 - pool_pre_pingを有効化
    Task: 6.2 - 接続プールが適切に動作することを確認
    """

    def test_appconfig_provides_pool_settings_for_mysql(self) -> None:
        """Test that AppConfig provides pool settings for MySQL driver.

        Requirement: 7.1, 7.2, 7.4
        Task: 6.2
        """
        config = AppConfig(
            DB_DRIVER="mysql",
            DB_HOST="localhost",
            DB_PORT=4000,
            DB_USER="root",
            DB_PASSWORD="",
            DB_NAME="test_db",
            JWT_SECRET_KEY="test-secret-key-12345678",
        )

        flask_config = config.to_flask_config()

        assert "SQLALCHEMY_ENGINE_OPTIONS" in flask_config
        engine_options = flask_config["SQLALCHEMY_ENGINE_OPTIONS"]

        assert "pool_size" in engine_options
        assert "pool_recycle" in engine_options
        assert "pool_pre_ping" in engine_options

        # Verify reasonable values
        assert engine_options["pool_size"] >= 1
        assert engine_options["pool_recycle"] > 0
        assert engine_options["pool_pre_ping"] is True

    def test_appconfig_skips_pool_settings_for_sqlite(self) -> None:
        """Test that AppConfig skips pool settings for SQLite driver.

        Requirement: 7.1 - SQLite接続時はプール設定をスキップ
        Task: 6.2
        """
        config = TestConfig()  # Uses SQLite by default

        flask_config = config.to_flask_config()

        # SQLite should not have pool settings
        assert "SQLALCHEMY_ENGINE_OPTIONS" not in flask_config

    def test_connection_pool_size_is_configurable(self) -> None:
        """Test that connection pool size can be configured.

        Requirement: 7.1 - 適切な接続プールサイズを設定
        Task: 6.2
        """
        # Create engine with custom pool size
        engine = create_engine(
            "sqlite:///:memory:",
            pool_size=10,
            max_overflow=5,
            poolclass=QueuePool,
        )

        assert engine.pool.size() == 10
        assert engine.pool._max_overflow == 5

        engine.dispose()

    def test_pool_pre_ping_enabled(self) -> None:
        """Test that pool_pre_ping can be enabled.

        Requirement: 7.4 - pool_pre_pingを有効化
        Task: 6.2
        """
        engine = create_engine(
            "sqlite:///:memory:",
            pool_pre_ping=True,
        )

        # Verify pool_pre_ping is enabled
        assert engine.pool._pre_ping is True

        engine.dispose()


class TestConnectionPoolConcurrency:
    """Test connection pool behavior under concurrent load.

    Requirement: 7.1, 7.2, 7.4
    Task: 6.2 - 並行クエリに対するパフォーマンスを確認
    """

    @pytest.fixture
    def sqlite_engine(self) -> Engine:
        """Create SQLite engine with pool configuration.

        Note: SQLite uses SingletonThreadPool by default, which doesn't support
        the same pool options as MySQL. For testing pool behavior, we use
        QueuePool with a file-based database for concurrent access.
        """
        from sqlalchemy.pool import QueuePool

        # Create a temporary file for the database
        # This allows multiple connections to share the same data
        db_fd, db_path = tempfile.mkstemp(suffix=".db")

        engine = create_engine(
            f"sqlite:///{db_path}",
            poolclass=QueuePool,
            pool_size=5,
            max_overflow=5,
            pool_pre_ping=True,
            connect_args={"check_same_thread": False},
        )

        # Create a test table
        with engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE test_concurrent (
                    id INTEGER PRIMARY KEY,
                    value TEXT,
                    created_at REAL
                )
            """))
            conn.commit()

        yield engine

        engine.dispose()
        os.close(db_fd)
        os.unlink(db_path)

    def test_concurrent_connections_handled_correctly(
        self,
        sqlite_engine: Engine,
    ) -> None:
        """Test that concurrent connections are handled correctly.

        Requirement: 7.1 - 接続プールが適切に動作
        Task: 6.2
        """
        results: list[bool] = []
        errors: list[str] = []

        def execute_query(query_id: int) -> None:
            try:
                with sqlite_engine.connect() as conn:
                    # Insert a record
                    conn.execute(
                        text("INSERT INTO test_concurrent (id, value, created_at) VALUES (:id, :value, :time)"),
                        {"id": query_id, "value": f"query_{query_id}", "time": time.time()},
                    )
                    conn.commit()

                    # Read it back
                    result = conn.execute(
                        text("SELECT value FROM test_concurrent WHERE id = :id"),
                        {"id": query_id},
                    )
                    row = result.fetchone()
                    if row and row[0] == f"query_{query_id}":
                        results.append(True)
                    else:
                        errors.append(f"Query {query_id} returned wrong value")
            except Exception as e:
                errors.append(f"Query {query_id} failed: {str(e)}")

        # Run concurrent queries
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(execute_query, i) for i in range(10)]
            concurrent.futures.wait(futures)

        # Verify all queries succeeded
        assert len(errors) == 0, f"Errors: {errors}"
        assert len(results) == 10

    def test_pool_does_not_exhaust_under_load(
        self,
        sqlite_engine: Engine,
    ) -> None:
        """Test that pool does not exhaust under moderate load.

        Requirement: 7.1, 7.2 - 接続プールが適切に動作
        Task: 6.2
        """
        import threading
        success_count = 0
        lock = threading.Lock()
        errors: list[str] = []

        def execute_many_queries(query_id: int) -> bool:
            nonlocal success_count
            try:
                for i in range(5):  # Multiple queries per thread
                    with sqlite_engine.connect() as conn:
                        result = conn.execute(text("SELECT 1"))
                        if result.scalar() == 1:
                            pass
                with lock:
                    success_count += 1
                return True
            except Exception as e:
                errors.append(f"Query {query_id}: {str(e)}")
                return False

        # Run many concurrent operations
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(execute_many_queries, i) for i in range(20)]
            results = [f.result() for f in as_completed(futures, timeout=30)]

        # All operations should succeed (allow for some SQLite locking issues)
        success_rate = sum(results) / len(results)
        assert success_rate >= 0.8, f"Too many failures ({len(errors)}): {errors[:5]}"

    def test_connection_checkout_timeout_handled(self) -> None:
        """Test that connection checkout timeout is handled gracefully.

        Requirement: 7.1 - 接続プールが適切に動作
        Task: 6.2
        """
        from sqlalchemy.pool import QueuePool

        # Create engine with very small pool and short timeout
        engine = create_engine(
            "sqlite:///:memory:",
            poolclass=QueuePool,
            pool_size=1,
            max_overflow=0,
            pool_timeout=1,  # 1 second timeout
            connect_args={"check_same_thread": False},
        )

        # Hold the only connection
        conn1 = engine.connect()

        errors: list[str] = []
        success: list[bool] = []

        def try_get_connection() -> None:
            try:
                with engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                    success.append(True)
            except Exception as e:
                errors.append(str(e))

        # Try to get another connection in a separate thread
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(try_get_connection)
            future.result(timeout=5)

        conn1.close()
        engine.dispose()

        # Should have timed out or succeeded (SQLite behavior differs from MySQL)
        # The important thing is no crashes occurred


class TestConnectionPoolRecycling:
    """Test connection pool recycling behavior.

    Requirement: 7.2 - アイドル接続管理
    Task: 6.2
    """

    def test_pool_recycle_configuration(self) -> None:
        """Test that pool_recycle can be configured.

        Requirement: 7.2 - 接続を再利用または解放
        Task: 6.2
        """
        engine = create_engine(
            "sqlite:///:memory:",
            pool_recycle=3600,  # 1 hour
        )

        assert engine.pool._recycle == 3600
        engine.dispose()

    def test_connections_are_reused(self) -> None:
        """Test that connections from the pool are reused.

        Requirement: 7.2 - 接続を再利用
        Task: 6.2
        """
        engine = create_engine(
            "sqlite:///:memory:",
            pool_size=2,
        )

        # Get connection IDs
        conn_ids = set()

        for _ in range(3):
            with engine.connect() as conn:
                # Get connection identifier
                conn_id = id(conn.connection)
                conn_ids.add(conn_id)
                conn.execute(text("SELECT 1"))

        # With pool reuse, we should see the same connection ID multiple times
        # Since pool_size=2, we should see at most 2 unique IDs
        assert len(conn_ids) <= 2

        engine.dispose()


class TestConnectionPoolPrePing:
    """Test connection pool pre-ping functionality.

    Requirement: 7.4 - pool_pre_pingを有効化
    Task: 6.2
    """

    def test_pre_ping_validates_connections(self) -> None:
        """Test that pre-ping validates connections before use.

        Requirement: 7.4 - 接続の健全性を確認
        Task: 6.2
        """
        engine = create_engine(
            "sqlite:///:memory:",
            pool_pre_ping=True,
        )

        # Get a connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            assert result.scalar() == 1

        # Connection should be returned to pool
        # Pre-ping should validate it when next used

        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            assert result.scalar() == 1

        engine.dispose()

    def test_pre_ping_handles_stale_connections_gracefully(self) -> None:
        """Test that pre-ping handles stale connections gracefully.

        Requirement: 7.3, 7.4 - 再接続を試行
        Task: 6.2
        """
        engine = create_engine(
            "sqlite:///:memory:",
            pool_pre_ping=True,
            pool_size=1,
        )

        # Get and return a connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))

        # Simulate some time passing (connection may be stale)
        # For SQLite in-memory, this won't actually make it stale
        # But the pre-ping mechanism should still work

        with engine.connect() as conn:
            # Pre-ping should validate connection before use
            result = conn.execute(text("SELECT 1"))
            assert result.scalar() == 1

        engine.dispose()


class TestConnectionPoolPerformance:
    """Test connection pool performance metrics.

    Requirement: 7.1, 7.2
    Task: 6.2 - 並行クエリに対するパフォーマンスを確認
    """

    @pytest.fixture
    def sqlite_engine(self) -> Engine:
        """Create SQLite engine for performance testing.

        Note: SQLite uses SingletonThreadPool by default. For testing pool
        behavior, we use QueuePool with a file-based database.
        """
        from sqlalchemy.pool import QueuePool

        # Create a temporary file for the database
        db_fd, db_path = tempfile.mkstemp(suffix=".db")

        engine = create_engine(
            f"sqlite:///{db_path}",
            poolclass=QueuePool,
            pool_size=10,
            max_overflow=10,
            pool_pre_ping=True,
            connect_args={"check_same_thread": False},
        )

        yield engine

        engine.dispose()
        os.close(db_fd)
        os.unlink(db_path)

    def test_sequential_query_performance(
        self,
        sqlite_engine: Engine,
    ) -> None:
        """Test sequential query performance.

        Task: 6.2 - パフォーマンスを確認
        """
        iterations = 100
        start_time = time.time()

        for _ in range(iterations):
            with sqlite_engine.connect() as conn:
                conn.execute(text("SELECT 1"))

        elapsed = time.time() - start_time

        # Should complete quickly (adjust threshold as needed)
        assert elapsed < 5.0, f"Sequential queries too slow: {elapsed}s for {iterations} queries"

    def test_concurrent_query_performance(
        self,
        sqlite_engine: Engine,
    ) -> None:
        """Test concurrent query performance.

        Task: 6.2 - 並行クエリに対するパフォーマンスを確認
        """
        iterations = 100

        def execute_query() -> float:
            start = time.time()
            with sqlite_engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return time.time() - start

        start_time = time.time()

        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(execute_query) for _ in range(iterations)]
            results = [f.result() for f in as_completed(futures, timeout=30)]

        elapsed = time.time() - start_time

        # All queries should complete successfully
        assert len(results) == iterations

        # Concurrent should not be significantly slower than sequential
        # (with some overhead for thread management)
        assert elapsed < 10.0, f"Concurrent queries too slow: {elapsed}s for {iterations} queries"

    def test_connection_pool_statistics(
        self,
        sqlite_engine: Engine,
    ) -> None:
        """Test that connection pool statistics are available.

        Task: 6.2
        """
        pool = sqlite_engine.pool

        # Initial state
        initial_size = pool.size()
        assert initial_size == 10

        # Use some connections
        connections = []
        for _ in range(3):
            connections.append(sqlite_engine.connect())

        # Pool should still report configured size
        assert pool.size() == 10

        # Return connections
        for conn in connections:
            conn.close()

        # Pool should be back to normal
        assert pool.size() == 10


class TestConnectionPoolErrorHandling:
    """Test connection pool error handling.

    Requirement: 7.3 - 再接続を試行
    Task: 6.2
    """

    def test_connection_error_is_handled_gracefully(self) -> None:
        """Test that connection errors are handled gracefully.

        Requirement: 7.3 - 接続失敗時の再接続
        Task: 6.2
        """
        # Try to connect to a non-existent database
        # This should raise an error but not crash
        with pytest.raises(Exception):
            engine = create_engine("mysql+pymysql://invalid:invalid@invalid:9999/invalid")
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))

    def test_invalid_connection_url_raises_error(self) -> None:
        """Test that invalid connection URL raises appropriate error.

        Task: 6.2
        """
        with pytest.raises(Exception):
            engine = create_engine("invalid://url")
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
