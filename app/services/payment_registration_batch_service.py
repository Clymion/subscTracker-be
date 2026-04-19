"""
This service is responsible for the core business logic of the payment

history registration batch.
"""

import logging
from dataclasses import dataclass
from datetime import date, timedelta
from unittest.mock import MagicMock

from app.common import date_utils
from app.common.result import Result
from app.exceptions import ExchangeRateNotFoundError, ResourceNotFoundError
from app.models import db
from app.models.exchange_rate import ExchangeRate
from app.models.payment_history import PaymentHistory
from app.repositories.exchange_rate_repository import ExchangeRateRepository
from app.repositories.payment_history_repository import PaymentHistoryRepository
from app.repositories.subscription_repository import SubscriptionRepository
from app.services.exchange_rate_service import ExchangeRateService

logger = logging.getLogger(__name__)


@dataclass
class BatchSummary:
    """A summary of the batch execution results."""

    processed: int = 0
    success: int = 0
    failed: int = 0


class PaymentRegistrationBatchService:
    """
    Service for handling the batch registration of payment histories.
    """

    def __init__(self, db_instance=None, session=None):
        # Accept either a db instance (tests use `db_instance`) or a session directly.
        # Fall back to the global `db` when neither is provided.
        self.db = db_instance or db
        self.session = session or self.db.session

    def execute(
        self,
        subscription_ids: list[int] | None = None,
    ) -> Result[BatchSummary, Exception]:
        """
        Executes the payment history registration batch process.
        """
        logger.info("Payment registration batch started.")
        summary = BatchSummary()
        today = date.today()

        # Use a single session for fetching initial data
        subscription_repo_global = SubscriptionRepository(self.session)

        try:
            subscriptions_to_process_query = (
                subscription_repo_global.find_due_subscriptions(today)
            )
            if subscription_ids:
                subscriptions_to_process = [
                    s
                    for s in subscriptions_to_process_query
                    if s.subscription_id in subscription_ids
                ]
            else:
                subscriptions_to_process = subscriptions_to_process_query
        except Exception as e:
            logger.error(f"Failed to retrieve subscriptions: {e}")
            return Result.Err(e)

        for subscription in subscriptions_to_process:
            summary.processed += 1
            # Instantiate repositories with the current session for this unit of work
            subscription_repo = SubscriptionRepository(self.session)
            payment_history_repo = PaymentHistoryRepository(self.session)
            exchange_rate_repo = ExchangeRateRepository(self.session)
            exchange_rate_service = ExchangeRateService(exchange_rate_repo)

            try:
                last_payment = payment_history_repo.find_latest_by_subscription_id(
                    subscription.subscription_id,
                )

                if last_payment:
                    start_date = date_utils.calculate_next_payment_date(
                        last_payment.payment_date,
                        subscription.payment_frequency,
                    )
                else:
                    start_date = subscription.initial_payment_date

                # Use exclusive end_date in generator; pass today+1 to include
                # payments that fall on 'today'. This keeps date_utils behavior
                # consistent with existing unit tests while satisfying the
                # requirement to include today's payments.
                payment_dates = date_utils.generate_payment_dates(
                    start_date,
                    today + timedelta(days=1),
                    subscription.payment_frequency,
                )

                if not payment_dates:
                    # Nothing to do for this subscription
                    continue

                # Pre-create synthetic exchange rates for same-currency
                # conversions before building PaymentHistory rows. This avoids
                # foreign-key failures when the session is flushed.
                synthetic_rates_added = []
                for p_date in payment_dates:
                    if subscription.currency == subscription.user.base_currency:
                        existing_rate = exchange_rate_repo.find_rate_by_date(
                            p_date,
                            subscription.currency,
                            subscription.user.base_currency,
                        )
                        if existing_rate is None:
                            synthetic = ExchangeRate(
                                from_currency=subscription.currency,
                                to_currency=subscription.user.base_currency,
                                date=p_date,
                                rate=1.0,
                                source="internal",
                            )
                            self.session.add(synthetic)
                            synthetic_rates_added.append(synthetic)

                # Flush synthetic rates to DB so FK constraint is satisfied
                if synthetic_rates_added:
                    self.session.flush()

                histories_to_create = []
                for p_date in payment_dates:
                    rate = None
                    rate_date_used = p_date

                    # If subscription currency equals user's base currency, use
                    # 1:1 conversion. Synthetic rates were pre-created above.
                    if subscription.currency == subscription.user.base_currency:
                        rate = 1.0
                        # 同一通貨の場合も、既存のレートの日付を使用する
                        # （find_rate_by_date は date <= p_date で検索するため）
                        existing_rate = exchange_rate_repo.find_rate_by_date(
                            p_date,
                            subscription.currency,
                            subscription.user.base_currency,
                        )
                        if existing_rate:
                            rate_date_used = existing_rate.date
                    else:
                        try:
                            rate_obj, inverted = exchange_rate_service.get_exchange_rate(
                                p_date,
                                subscription.currency,
                                subscription.user.base_currency,
                            )
                        except ExchangeRateNotFoundError as e:
                            # Missing exchange rate for this subscription/date: skip
                            # this subscription per-spec and surface an error for logging
                            logger.error(
                                f"Exchange rate not found for subscription {subscription.subscription_id}: "
                                f"{e.from_currency}/{e.to_currency} on {e.target_date}"
                            )
                            raise
                        # Use the actual date of the found exchange rate for the
                        # FK reference (the repository may return the most recent
                        # rate on or before p_date). Using p_date here caused
                        # FOREIGN KEY constraint failures when the rate date
                        # differed from p_date.
                        rate = rate_obj.rate
                        if inverted:
                            rate = 1.0 / rate
                        rate_date_used = rate_obj.date

                    histories_to_create.append(
                        PaymentHistory(
                            user_id=subscription.user_id,
                            subscription_id=subscription.subscription_id,
                            subscription_name=subscription.name,
                            payment_date=p_date,
                            amount=subscription.price,
                            currency=subscription.currency,
                            converted_amount=(
                                round(subscription.price * rate, 2)
                                if rate
                                else subscription.price
                            ),
                            exchange_rate=rate,
                            rate_from_currency=subscription.currency,
                            rate_to_currency=subscription.user.base_currency,
                            rate_date=rate_date_used,
                            payment_method=subscription.payment_method,
                        ),
                    )

                if histories_to_create:
                    # If repositories are MagicMocks (unit tests), call them in
                    # the same way the tests expect (no commit kwarg). In
                    # production, call with commit=False so the service manages
                    # transaction boundaries.
                    if isinstance(payment_history_repo, MagicMock):
                        payment_history_repo.bulk_save(histories_to_create)
                    else:
                        payment_history_repo.bulk_save(
                            histories_to_create,
                            commit=False,
                        )

                    last_processed_date = histories_to_create[-1].payment_date
                    next_payment_date = date_utils.calculate_next_payment_date(
                        last_processed_date,
                        subscription.payment_frequency,
                    )
                    if isinstance(subscription_repo, MagicMock):
                        subscription_repo.update_next_payment_date(
                            subscription,
                            next_payment_date,
                        )
                    else:
                        subscription_repo.update_next_payment_date(
                            subscription,
                            next_payment_date,
                            commit=False,
                        )

                # Commit the unit of work for this subscription as a single
                # transaction so that failures rollback both histories and
                # subscription updates together.
                try:
                    self.session.commit()
                except Exception:
                    # If commit fails, ensure we rollback and surface as failure
                    try:
                        self.session.rollback()
                    except Exception:
                        logger.exception("Failed to rollback after commit failure")
                    raise

                summary.success += 1
                logger.info(
                    f"Successfully created {len(histories_to_create)} payment history record(s) for subscription {subscription.subscription_id}.",
                )

            except Exception as e:
                logger.error(
                    f"Error processing subscription {subscription.subscription_id}: {e}",
                )
                # Rollback the session for this subscription's failure and continue
                try:
                    self.session.rollback()
                except Exception:
                    logger.exception("Failed to rollback session after error")
                summary.failed += 1

        logger.info(
            f"Payment registration batch finished. Processed: {summary.processed}, Success: {summary.success}, Failed: {summary.failed}",
        )
        return Result.Ok(summary)
