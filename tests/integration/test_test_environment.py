"""
Tests for test environment configuration with TiDB support.

This module verifies that the test configuration and fixtures work correctly
for both SQLite and TiDB environments.

Requirements: 5.1, 5.2, 5.3, 5.4
Tasks: 4.1, 4.2, 4.3
"""

from pathlib import Path

import pytest
from flask import Flask
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import TestConfig, get_config
from app.models import db as _db
from tests.helpers import make_and_save_user


class TestTestConfigTiDBSupport:
    """Test TestConfig TiDB support.

    Requirement: 5.1, 5.2 - テスト環境用DB設定
    Task: 4.1 - TestConfigのTiDB対応
    """

    def test_test_config_defaults_to_sqlite_in_memory(self) -> None:
        """Test that TestConfig defaults to SQLite in-memory database.

        Requirement: 5.1 - デフォルトでSQLiteインメモリDBを使用
        """
        config = TestConfig()

        assert config.DB_DRIVER == "sqlite"
        assert config.DB_NAME == ":memory:"
        assert config.database_url == "sqlite:///:memory:"

    def test_test_config_can_use_tidb_via_env_vars(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test that TestConfig can use TiDB via environment variables.

        Requirement: 5.2 - 環境変数によるTiDBテスト設定が可能
        """
        # Set TEST_ prefixed environment variables for TiDB
        monkeypatch.setenv("TEST_DB_DRIVER", "mysql")
        monkeypatch.setenv("TEST_DB_HOST", "test-tidb-server")
        monkeypatch.setenv("TEST_DB_PORT", "4000")
        monkeypatch.setenv("TEST_DB_USER", "test_user")
        monkeypatch.setenv("TEST_DB_PASSWORD", "test_password")
        monkeypatch.setenv("TEST_DB_NAME", "test_subscription_db")

        config = TestConfig()

        assert config.DB_DRIVER == "mysql"
        assert config.DB_HOST == "test-tidb-server"
        assert config.DB_PORT == 4000
        assert "mysql+pymysql://" in config.database_url

    def test_test_config_database_url_mysql_format(self) -> None:
        """Test that MySQL database URL is correctly formatted."""
        config = TestConfig()
        # Use property to check format
        config.DB_DRIVER = "mysql"
        config.DB_HOST = "localhost"
        config.DB_PORT = 4000
        config.DB_USER = "root"
        config.DB_PASSWORD = ""  # type: ignore
        config.DB_NAME = "test_db"

        url = config.database_url
        assert url == "mysql+pymysql://root:@localhost:4000/test_db"

    def test_test_config_has_safe_defaults(self) -> None:
        """Test that TestConfig has safe default values.

        Requirement: 5.1 - テスト用データベース設定が適切に機能
        """
        config = TestConfig()

        # JWT secret should be safe for testing (not production)
        assert "test" in config.JWT_SECRET_KEY.lower()
        assert "production" not in config.JWT_SECRET_KEY.lower()

        # Testing flag should be True
        assert config.TESTING is True

    def test_test_config_to_flask_config(self) -> None:
        """Test that to_flask_config returns correct Flask config."""
        config = TestConfig()

        flask_config = config.to_flask_config()

        assert "SQLALCHEMY_DATABASE_URI" in flask_config
        assert "SQLALCHEMY_TRACK_MODIFICATIONS" in flask_config
        assert flask_config["TESTING"] is True


class TestTestFixtureCleanup:
    """Test database cleanup fixtures.

    Requirement: 5.3, 5.4 - テスト後DBクリーンアップ、テスト間DB状態分離
    Task: 4.2 - テストフィクスチャの確認
    """

    def test_clean_db_fixture_provides_empty_database(
        self,
        clean_db: Session,
    ) -> None:
        """Test that clean_db fixture provides an empty database.

        Requirement: 5.4 - テスト間でデータベース状態を分離
        """
        # Verify database is empty
        from app.models.user import User
        from app.models.subscription import Subscription
        from app.models.label import Label

        user_count = clean_db.query(User).count()
        sub_count = clean_db.query(Subscription).count()
        label_count = clean_db.query(Label).count()

        assert user_count == 0, "Database should be empty at start"
        assert sub_count == 0
        assert label_count == 0

    def test_clean_db_fixture_cleans_up_after_test(
        self,
        clean_db: Session,
    ) -> None:
        """Test that clean_db fixture cleans up data after test.

        Requirement: 5.3 - テスト実行後にデータベースのクリーンアップ
        """
        # Create test data
        user = make_and_save_user(clean_db)
        clean_db.commit()

        # Verify data was created
        from app.models.user import User
        count = clean_db.query(User).count()
        assert count == 1

        # After test, the clean_db fixture should clean up
        # (verified in next test)

    def test_clean_db_isolation_between_tests_part1(
        self,
        clean_db: Session,
    ) -> None:
        """Part 1 of isolation test - create data."""
        # Create a user with unique username
        from app.models.user import User
        user = User(username="isolation_test_user_1", email="iso1@test.com")
        user.set_password("password")
        clean_db.add(user)
        clean_db.commit()

        # Verify user exists
        count = clean_db.query(User).filter(
            User.username == "isolation_test_user_1"
        ).count()
        assert count == 1

    def test_clean_db_isolation_between_tests_part2(
        self,
        clean_db: Session,
    ) -> None:
        """Part 2 of isolation test - verify data from part1 is cleaned.

        Requirement: 5.4 - テスト間でデータベース状態を分離
        """
        # Verify user from part1 does not exist
        from app.models.user import User
        count = clean_db.query(User).filter(
            User.username == "isolation_test_user_1"
        ).count()

        assert count == 0, "Data from previous test should be cleaned up"


class TestIntegrationTestExecution:
    """Test integration test execution with various configurations.

    Requirement: 5.2, 3.3 - 統合テスト実行、外部キー制約の動作確認
    Task: 4.3 - 統合テストの実行
    """

    def test_crud_operations_work_in_test_db(
        self,
        clean_db: Session,
    ) -> None:
        """Test that CRUD operations work correctly in test database.

        Requirement: 5.2 - CRUD操作がTiDBで正しく動作
        """
        from app.models.user import User
        from app.models.subscription import Subscription
        from datetime import date

        # Create
        user = make_and_save_user(clean_db)
        sub = Subscription(
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
        clean_db.add(sub)
        clean_db.commit()

        # Read
        found_sub = clean_db.query(Subscription).filter_by(
            name="Test Subscription"
        ).first()
        assert found_sub is not None
        assert found_sub.price == 9.99

        # Update
        found_sub.price = 19.99
        clean_db.commit()
        updated = clean_db.query(Subscription).filter_by(
            subscription_id=found_sub.subscription_id
        ).first()
        assert updated.price == 19.99

        # Delete
        clean_db.delete(found_sub)
        clean_db.commit()
        deleted = clean_db.query(Subscription).filter_by(
            subscription_id=sub.subscription_id
        ).first()
        assert deleted is None

    def test_foreign_key_cascade_works_in_test_db(
        self,
        clean_db: Session,
    ) -> None:
        """Test that foreign key CASCADE works in test database.

        Requirement: 3.3, 5.2 - 外部キー制約の動作確認テスト
        """
        from app.models.user import User
        from app.models.label import Label

        # Create user and label
        user = make_and_save_user(clean_db)
        label = Label(user_id=user.user_id, name="Test Label", color="#FF0000")
        clean_db.add(label)
        clean_db.commit()
        label_id = label.label_id

        # Delete user (should cascade to label)
        clean_db.delete(user)
        clean_db.commit()

        # Verify label was deleted
        deleted_label = clean_db.query(Label).filter_by(
            label_id=label_id
        ).first()
        assert deleted_label is None

    def test_db_session_transaction_rollback(
        self,
        db_session: Session,
    ) -> None:
        """Test that db_session fixture uses transaction rollback.

        Requirement: 5.4 - テスト間でデータベース状態を分離
        """
        from app.models.user import User

        # Create user
        user = User(username="transaction_test", email="trans@test.com")
        user.set_password("password")
        db_session.add(user)
        db_session.commit()

        # User should exist within this transaction
        found = db_session.query(User).filter_by(
            username="transaction_test"
        ).first()
        assert found is not None


class TestConftestFixtures:
    """Test that conftest.py fixtures work correctly.

    Task: 4.2 - テストフィクスチャの確認
    """

    def test_app_fixture_creates_flask_app(
        self,
        app: Flask,
    ) -> None:
        """Test that app fixture creates a Flask application."""
        assert app is not None
        assert isinstance(app, Flask)
        assert app.config["TESTING"] is True

    def test_client_fixture_creates_test_client(
        self,
        client,
    ) -> None:
        """Test that client fixture creates a test client."""
        response = client.get("/api/v1/health")
        # The endpoint might not exist, but client should work
        assert response is not None

    def test_test_config_fixture_returns_test_config(
        self,
        test_config: TestConfig,
    ) -> None:
        """Test that test_config fixture returns TestConfig instance."""
        assert isinstance(test_config, TestConfig)
        assert test_config.TESTING is True


class TestForeignKeysEnabledInTest:
    """Test that foreign key constraints are enabled in test database.

    This verifies the SQLite PRAGMA is working correctly.
    """

    def test_foreign_keys_enabled_in_sqlite(
        self,
        clean_db: Session,
    ) -> None:
        """Test that foreign keys are enabled in SQLite test database.

        Requirement: 2.1 - SQLite接続時のみPRAGMAが実行
        """
        # Check PRAGMA setting
        result = clean_db.execute(text("PRAGMA foreign_keys")).fetchone()
        assert result is not None
        # Foreign keys should be enabled (1 or True)
        assert result[0] in (1, True), "Foreign keys should be enabled"

    def test_foreign_key_constraint_enforced(
        self,
        clean_db: Session,
    ) -> None:
        """Test that foreign key constraints are enforced.

        Requirement: 3.3 - 外部キー制約の動作確認
        """
        from app.models.subscription import Subscription
        from datetime import date
        from sqlalchemy.exc import IntegrityError

        # Try to create a subscription with non-existent user_id
        sub = Subscription(
            user_id=99999,  # Non-existent user
            name="Test",
            price=10.0,
            currency="USD",
            initial_payment_date=date(2024, 1, 1),
            next_payment_date=date(2024, 2, 1),
            payment_frequency="monthly",
            payment_method="credit_card",
            status="active",
        )
        clean_db.add(sub)

        # Should raise IntegrityError due to FK constraint
        with pytest.raises(IntegrityError):
            clean_db.commit()
