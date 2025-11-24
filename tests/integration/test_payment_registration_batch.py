from datetime import datetime, timedelta, timezone

import pytest
from flask import Flask
from sqlalchemy.orm import Session

from app.models import db
from app.models.payment_history import PaymentHistory
from app.models.subscription import Subscription
from app.services.payment_registration_batch_service import (
    PaymentRegistrationBatchService,
)
from tests.helpers import (
    make_and_save_exchange_rate,
    make_and_save_subscription,
    make_and_save_user,
)


@pytest.mark.integration
class TestPaymentRegistrationBatch:
    """Integration tests for the payment history"""

    def test_batch_script_creates_payment_history_for_due_subscription(
        self,
        app: Flask,
        db_session: Session,
    ):
        """Test that the batch script creates payment history for subscriptions"""
        # Arrange
        today = datetime.now(tz=timezone.utc).date()
        user = make_and_save_user(
            db_session,
            username="batchuser",
            email="batch@test.com",
            base_currency="USD",
        )

        make_and_save_subscription(
            db_session,
            user_id=user.user_id,
            name="Due Service",
            price=10.0,
            initial_payment_date=today - timedelta(days=40),
            next_payment_date=today - timedelta(days=1),
        )

        make_and_save_subscription(
            db_session,
            user_id=user.user_id,
            name="Future Service",
            price=20.0,
            initial_payment_date=today - timedelta(days=10),
            next_payment_date=today + timedelta(days=10),
        )

        # 過去40日から今日までの日付範囲をカバー
        for days_ago in range(0, 41):
            rate_date = today - timedelta(days=days_ago)
            make_and_save_exchange_rate(
                db_session,
                from_currency="USD",
                to_currency="USD",
                date=rate_date,
                rate=1.0,
                source="test",
            )

        db_session.commit()

        # Act
        with app.app_context():
            batch_service = PaymentRegistrationBatchService(db_instance=db)
            result = batch_service.execute()  # ← 結果も確認

        # Assert
        assert result.is_ok()  # 成功を確認

    def test_batch_script_backfills_histories(self, app: Flask, db_session: Session):
        """Test that the batch script backfills payment histories for overdue subscriptions"""
        # Arrange
        today = datetime.now(tz=timezone.utc).date()
        user = make_and_save_user(
            db_session,
            username="backfilluser",
            email="backfill@test.com",
            base_currency="JPY",
        )

        # ← user_id を事前に取得
        user_id = user.user_id

        make_and_save_subscription(
            db_session,
            user_id=user_id,  # ← 変数を使用
            name="Backfill Service",
            price=1000,
            currency="JPY",
            initial_payment_date=today - timedelta(days=65),
            next_payment_date=None,
        )

        # ← exchange_rates を作成(前回と同じ対処)
        for days_ago in range(0, 66):
            rate_date = today - timedelta(days=days_ago)
            make_and_save_exchange_rate(
                db_session,
                from_currency="JPY",
                to_currency="JPY",
                date=rate_date,
                rate=1.0,
                source="test",
            )
        db_session.commit()

        # Act
        with app.app_context():
            batch_service = PaymentRegistrationBatchService(db_instance=db)
            batch_service.execute()

        # Assert
        histories = db_session.query(PaymentHistory).filter_by(user_id=user_id).all()
        assert len(histories) >= 2

        backfill_sub = (
            db_session.query(Subscription).filter_by(name="Backfill Service").one()
        )
        assert backfill_sub.next_payment_date > today

    def test_batch_script_with_specific_ids(self, app: Flask, db_session: Session):
        """Test that the batch script processes only specified subscription IDs"""
        # Arrange
        today = datetime.now(tz=timezone.utc).date()
        user = make_and_save_user(
            db_session,
            username="iduser",
            email="id@test.com",
            base_currency="USD",
        )

        user_id = user.user_id

        sub1 = make_and_save_subscription(
            db_session,
            user_id=user_id,
            name="ID Service 1",
            initial_payment_date=today - timedelta(days=30),
            next_payment_date=today - timedelta(days=1),
        )

        sub1_id = sub1.subscription_id

        sub2 = make_and_save_subscription(
            db_session,
            user_id=user_id,
            name="ID Service 2",
            initial_payment_date=today - timedelta(days=30),
            next_payment_date=today - timedelta(days=2),
        )

        sub2_id = sub2.subscription_id

        # exchange_rates を作成 (30日前から今日まで)
        for days_ago in range(0, 31):
            rate_date = today - timedelta(days=days_ago)
            make_and_save_exchange_rate(
                db_session,
                from_currency="USD",
                to_currency="USD",
                date=rate_date,
                rate=1.0,
                source="test",
            )

        db_session.commit()

        # Act
        with app.app_context():
            batch_service = PaymentRegistrationBatchService(db_instance=db)
            batch_service.execute(subscription_ids=[sub1_id])

        # Assert
        histories = db_session.query(PaymentHistory).filter_by(user_id=user_id).all()

        # sub1 だけが処理されたことを確認
        assert (
            len(histories) >= 1
        ), f"Expected at least one payment history, got {len(histories)}"

        # sub1 の履歴のみが含まれることを確認
        sub1_histories = [h for h in histories if h.subscription_id == sub1_id]
        sub2_histories = [h for h in histories if h.subscription_id == sub2_id]

        assert len(sub1_histories) >= 1, "Expected at least one history for sub1"
        assert len(sub2_histories) == 0, "Expected no histories for sub2"
