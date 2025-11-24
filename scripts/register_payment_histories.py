import argparse
import fcntl
import logging
import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from app.models import db

# Explicitly import all models to ensure they are registered with SQLAlchemy
from app.services.payment_registration_batch_service import (
    PaymentRegistrationBatchService,
)

# Configure logging for the batch script
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Register payment histories for subscriptions.",
    )
    parser.add_argument(
        "--subscription-ids",
        type=str,
        help="Comma-separated list of subscription IDs to process. If not provided, all due subscriptions will be processed.",
    )
    return parser.parse_args()


def run_batch() -> argparse.NoReturn:
    """Run the payment registration batch script."""
    args = parse_args()
    # Acquire an exclusive filesystem lock to prevent concurrent executions
    lock_path = "/tmp/register_payment_histories.lock"
    lock_file = open(lock_path, "w")
    try:
        fcntl.flock(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        logger.error(
            "Another instance of the payment registration batch is already running. Exiting.",
        )
        sys.exit(1)

    try:
        app = create_app()

        with app.app_context():
            # If running in a test environment with an in-memory DB, create tables.
            if app.config["TESTING"] and "sqlite:///:memory:" in str(
                app.config["SQLALCHEMY_DATABASE_URI"],
            ):
                db.create_all()

            logger.info("Starting payment registration batch script.")

            # Instantiate service
            batch_service = PaymentRegistrationBatchService()

            subscription_ids = None
            if args.subscription_ids:
                try:
                    subscription_ids = [
                        int(s_id.strip()) for s_id in args.subscription_ids.split(",")
                    ]
                    logger.info(
                        f"Processing specific subscription IDs: {subscription_ids}",
                    )
                except ValueError:
                    logger.error(
                        "Invalid subscription IDs provided. Please provide a comma-separated list of integers.",
                    )
                    sys.exit(1)

            result = batch_service.execute(subscription_ids=subscription_ids)

            if result.is_ok():
                summary = result.unwrap()
                logger.info(
                    f"Batch finished: Processed={summary.processed}, Success={summary.success}, Failed={summary.failed}",
                )
                # In a real scenario, you might want a different exit code based on summary.
                sys.exit(0)
            else:
                error = result.unwrap_err()
                logger.error(f"Batch failed with an unhandled error: {error}")
                sys.exit(1)
    finally:
        try:
            fcntl.flock(lock_file, fcntl.LOCK_UN)
        except Exception:
            pass
        try:
            lock_file.close()
        except Exception:
            pass


if __name__ == "__main__":
    run_batch()
