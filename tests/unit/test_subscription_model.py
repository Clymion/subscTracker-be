"""
Unit tests for Subscription model.

Tests subscription creation, validation, relationships, and business logic
following the test list from docs/test-list/subscription-model.md
"""

from collections.abc import Generator
from datetime import date

import pytest
from sqlalchemy.orm import Session

from app.constants import (
    ErrorMessages,
    PaymentFrequency,
    SubscriptionStatus,
)
from app.models.subscription import Subscription
from tests.helpers import make_and_save_user


@pytest.mark.unit
class TestSubscriptionModelCreation:
    """Test Subscription model creation and basic attributes."""

    def test_subscription_creation_with_all_required_fields(
        self,
        clean_db: Generator[Session, None, None],
    ):
        """Test creating a subscription with all required fields."""
        # Arrange
        user = make_and_save_user(
            clean_db,
            username="testuser",
            email="test@example.com",
        )

        # Act
        subscription = Subscription(
            user_id=user.user_id,
            name="Netflix Premium",
            price=15.99,
            currency="USD",
            initial_payment_date=date(2024, 1, 15),
            next_payment_date=date(2024, 2, 15),
            payment_frequency="monthly",
            payment_method="credit_card",
            status="active",
        )

        # Assert
        assert subscription.user_id == user.user_id
        assert subscription.name == "Netflix Premium"
        assert subscription.price == 15.99
        assert subscription.currency == "USD"
        assert subscription.initial_payment_date == date(2024, 1, 15)
        assert subscription.next_payment_date == date(2024, 2, 15)
        assert subscription.payment_frequency == "monthly"
        assert subscription.payment_method == "credit_card"
        assert subscription.status == "active"

    def test_subscription_creation_with_minimal_required_fields(
        self,
        clean_db: Generator[Session, None, None],
    ):
        """Test creating a subscription with minimal required fields."""
        # Arrange
        user = make_and_save_user(clean_db)

        # Act
        subscription = Subscription(
            user_id=user.user_id,
            name="Basic Service",
            price=9.99,
            currency="USD",
            initial_payment_date=date(2024, 1, 1),
            next_payment_date=date(2024, 2, 1),
            payment_frequency="monthly",
            payment_method="credit_card",
            status="trial",
        )

        # Assert
        assert subscription.user_id == user.user_id
        assert subscription.name == "Basic Service"
        assert subscription.url is None
        assert subscription.notes is None
        assert subscription.image_url is None

    def test_subscription_creation_with_all_optional_fields(
        self,
        clean_db: Generator[Session, None, None],
    ):
        """Test creating a subscription with all optional fields included."""
        # Arrange
        user = make_and_save_user(clean_db)

        # Act
        subscription = Subscription(
            user_id=user.user_id,
            name="Premium Service",
            price=29.99,
            currency="USD",
            initial_payment_date=date(2024, 1, 1),
            next_payment_date=date(2024, 2, 1),
            payment_frequency="monthly",
            payment_method="credit_card",
            status="active",
            url="https://example.com",
            notes="Annual discount applied",
            image_url="https://example.com/logo.png",
        )

        # Assert
        assert subscription.url == "https://example.com"
        assert subscription.notes == "Annual discount applied"
        assert subscription.image_url == "https://example.com/logo.png"

    def test_subscription_string_representations(
        self,
        clean_db: Generator[Session, None, None],
    ):
        """Test subscription string representation methods."""
        # Arrange
        user = make_and_save_user(clean_db)
        subscription = Subscription(
            user_id=user.user_id,
            name="Test Service",
            price=19.99,
            currency="USD",
            initial_payment_date=date(2024, 1, 1),
            next_payment_date=date(2024, 2, 1),
            payment_frequency="monthly",
            payment_method="credit_card",
            status="active",
        )

        # Act & Assert
        assert str(subscription) == "Test Service (active)"
        assert repr(subscription) == "<Subscription Test Service - USD19.99>"


@pytest.mark.unit
class TestSubscriptionFieldValidation:
    """Test Subscription model field validation."""

    def test_validate_currency_with_valid_currencies(self):
        """Test currency validation with valid USD and JPY."""
        # Arrange & Act & Assert
        for currency in ["USD", "JPY"]:
            subscription = Subscription(currency=currency)
            subscription.validate_currency()  # Should not raise

    def test_validate_currency_with_invalid_currency(self):
        """Test currency validation with invalid currency."""
        # Arrange
        subscription = Subscription(currency="EUR")

        # Act & Assert
        with pytest.raises(ValueError, match=ErrorMessages.UNSUPPORTED_CURRENCY):
            subscription.validate_currency()

    def test_validate_status_with_valid_statuses(self):
        """Test status validation with all valid status values."""
        # Arrange & Act & Assert
        valid_statuses = ["trial", "active", "suspended", "cancelled", "expired"]
        for status in valid_statuses:
            subscription = Subscription(status=status)
            subscription.validate_status()  # Should not raise

    def test_validate_status_with_invalid_status(self):
        """Test status validation with invalid status."""
        # Arrange
        subscription = Subscription(status="invalid_status")

        # Act & Assert
        with pytest.raises(ValueError, match=ErrorMessages.INVALID_STATUS):
            subscription.validate_status()

    def test_validate_payment_frequency_with_valid_frequencies(self):
        """Test payment frequency validation with valid values."""
        # Arrange & Act & Assert
        valid_frequencies = ["monthly", "quarterly", "yearly"]
        for frequency in valid_frequencies:
            subscription = Subscription(payment_frequency=frequency)
            subscription.validate_payment_frequency()  # Should not raise

    def test_validate_payment_frequency_with_invalid_frequency(self):
        """Test payment frequency validation with invalid value."""
        # Arrange
        subscription = Subscription(payment_frequency="weekly")

        # Act & Assert
        with pytest.raises(ValueError, match=ErrorMessages.INVALID_PAYMENT_FREQUENCY):
            subscription.validate_payment_frequency()

    def test_validate_price_with_positive_values(self):
        """Test price validation with positive values."""
        # Arrange & Act & Assert
        positive_prices = [0.01, 1.0, 9.99, 100.50, 999.99]
        for price in positive_prices:
            subscription = Subscription(price=price)
            subscription.validate_price()  # Should not raise

    def test_validate_price_with_zero_or_negative_values(self):
        """Test price validation with zero or negative values."""
        # Arrange & Act & Assert
        invalid_prices = [0, -0.01, -1.0, -100.0]
        for price in invalid_prices:
            subscription = Subscription(price=price)
            with pytest.raises(ValueError, match=ErrorMessages.PRICE_MUST_BE_POSITIVE):
                subscription.validate_price()

    def test_validate_dates_with_valid_date_order(self):
        """Test date validation with proper date ordering."""
        # Arrange
        subscription = Subscription(
            initial_payment_date=date(2024, 1, 15),
            next_payment_date=date(2024, 2, 15),
        )

        # Act & Assert
        subscription.validate_dates()  # Should not raise

    def test_validate_dates_with_invalid_date_order(self):
        """Test date validation with next payment before initial payment."""
        # Arrange
        subscription = Subscription(
            initial_payment_date=date(2024, 2, 15),
            next_payment_date=date(2024, 1, 15),  # Before initial date
        )

        # Act & Assert
        with pytest.raises(
            ValueError,
            match=ErrorMessages.NEXT_PAYMENT_DATE_BEFORE_INITIAL,
        ):
            subscription.validate_dates()


@pytest.mark.unit
class TestSubscriptionBusinessLogic:
    """Test Subscription model business logic methods."""

    def test_is_active_with_active_status(self):
        """Test is_active() returns True for active subscriptions."""
        # Arrange
        subscription = Subscription(status=SubscriptionStatus.ACTIVE)

        # Act & Assert
        assert subscription.is_active() is True

    def test_is_active_with_inactive_statuses(self):
        """Test is_active() returns False for non-active subscriptions."""
        # Arrange & Act & Assert
        inactive_statuses = [
            SubscriptionStatus.TRIAL,
            SubscriptionStatus.SUSPENDED,
            SubscriptionStatus.CANCELLED,
            SubscriptionStatus.EXPIRED,
        ]
        for status in inactive_statuses:
            subscription = Subscription(status=status)
            assert subscription.is_active() is False

    def test_monthly_cost_calculation_for_different_frequencies(self):
        """Test monthly cost calculation for all payment frequencies."""
        # Test monthly subscription
        monthly_sub = Subscription(
            price=10.0,
            payment_frequency=PaymentFrequency.MONTHLY,
        )
        assert monthly_sub.monthly_cost() == 10.0

        # Test quarterly subscription
        quarterly_sub = Subscription(
            price=30.0,
            payment_frequency=PaymentFrequency.QUARTERLY,
        )
        assert quarterly_sub.monthly_cost() == 10.0  # 30/3

        # Test yearly subscription
        yearly_sub = Subscription(
            price=120.0,
            payment_frequency=PaymentFrequency.YEARLY,
        )
        assert yearly_sub.monthly_cost() == 10.0  # 120/12

    def test_yearly_cost_calculation_for_different_frequencies(self):
        """Test yearly cost calculation for all payment frequencies."""
        # Test monthly subscription
        monthly_sub = Subscription(
            price=10.0,
            payment_frequency=PaymentFrequency.MONTHLY,
        )
        assert monthly_sub.yearly_cost() == 120.0  # 10*12

        # Test quarterly subscription
        quarterly_sub = Subscription(
            price=30.0,
            payment_frequency=PaymentFrequency.QUARTERLY,
        )
        assert quarterly_sub.yearly_cost() == 120.0  # 30*4

        # Test yearly subscription
        yearly_sub = Subscription(
            price=120.0,
            payment_frequency=PaymentFrequency.YEARLY,
        )
        assert yearly_sub.yearly_cost() == 120.0

    def test_cost_calculation_with_invalid_frequency(self):
        """Test cost calculation methods with invalid payment frequency."""
        # Arrange
        subscription = Subscription(price=10.0, payment_frequency="invalid")

        # Act & Assert
        with pytest.raises(ValueError, match=ErrorMessages.UNKNOWN_PAYMENT_FREQUENCY):
            subscription.monthly_cost()

        with pytest.raises(ValueError, match=ErrorMessages.UNKNOWN_PAYMENT_FREQUENCY):
            subscription.yearly_cost()


@pytest.mark.unit
class TestSubscriptionPaymentDateCalculation:
    """Test Subscription model payment date calculation logic."""

    def test_calculate_next_payment_date_monthly(self):
        """Test next payment date calculation for monthly frequency."""
        # Arrange
        subscription = Subscription(
            payment_frequency=PaymentFrequency.MONTHLY,
            next_payment_date=date(2024, 1, 15),
        )

        # Act
        next_date = subscription.calculate_next_payment_date()

        # Assert
        assert next_date == date(2024, 2, 15)

    def test_calculate_next_payment_date_quarterly(self):
        """Test next payment date calculation for quarterly frequency."""
        # Arrange
        subscription = Subscription(
            payment_frequency=PaymentFrequency.QUARTERLY,
            next_payment_date=date(2024, 1, 15),
        )

        # Act
        next_date = subscription.calculate_next_payment_date()

        # Assert
        assert next_date == date(2024, 4, 15)

    def test_calculate_next_payment_date_yearly(self):
        """Test next payment date calculation for yearly frequency."""
        # Arrange
        subscription = Subscription(
            payment_frequency=PaymentFrequency.YEARLY,
            next_payment_date=date(2024, 1, 15),
        )

        # Act
        next_date = subscription.calculate_next_payment_date()

        # Assert
        assert next_date == date(2025, 1, 15)

    def test_calculate_next_payment_date_with_custom_from_date(self):
        """Test next payment date calculation with custom from_date."""
        # Arrange
        subscription = Subscription(
            payment_frequency=PaymentFrequency.MONTHLY,
            next_payment_date=date(2024, 1, 15),  # This should be ignored
        )

        # Act
        next_date = subscription.calculate_next_payment_date(
            from_date=date(2024, 3, 10),
        )

        # Assert
        assert next_date == date(2024, 4, 10)

    def test_smart_month_end_handling_jan_31_to_feb(self):
        """Test smart month-end handling for Jan 31 -> Feb."""
        # Arrange
        subscription = Subscription(
            payment_frequency=PaymentFrequency.MONTHLY,
            next_payment_date=date(2024, 1, 31),  # Last day of January
        )

        # Act
        next_date = subscription.calculate_next_payment_date()

        # Assert - Feb 2024 has 29 days (leap year)
        assert next_date == date(2024, 2, 29)

    def test_smart_month_end_handling_jan_31_to_feb_non_leap_year(self):
        """Test smart month-end handling for Jan 31 -> Feb in non-leap year."""
        # Arrange
        subscription = Subscription(
            payment_frequency=PaymentFrequency.MONTHLY,
            next_payment_date=date(2023, 1, 31),  # Last day of January (non-leap year)
        )

        # Act
        next_date = subscription.calculate_next_payment_date()

        # Assert - Feb 2023 has 28 days
        assert next_date == date(2023, 2, 28)

    def test_smart_month_end_handling_may_31_to_june(self):
        """Test smart month-end handling for May 31 -> June."""
        # Arrange
        subscription = Subscription(
            payment_frequency=PaymentFrequency.MONTHLY,
            next_payment_date=date(2024, 5, 31),  # Last day of May
        )

        # Act
        next_date = subscription.calculate_next_payment_date()

        # Assert - June has 30 days
        assert next_date == date(2024, 6, 30)

    def test_smart_month_end_handling_preserves_end_of_month(self):
        """Test that end-of-month contracts stay end-of-month."""
        # Arrange
        subscription = Subscription(
            payment_frequency=PaymentFrequency.MONTHLY,
            next_payment_date=date(2024, 3, 31),  # Last day of March
        )

        # Act
        next_date = subscription.calculate_next_payment_date()

        # Assert - April has 30 days, but next month (May) should go to May 31
        assert next_date == date(2024, 4, 30)

        # Test another month forward
        subscription.next_payment_date = next_date
        next_date_2 = subscription.calculate_next_payment_date()
        assert next_date_2 == date(2024, 5, 31)  # Back to end of month

    def test_calculate_next_payment_date_with_invalid_frequency(self):
        """Test payment date calculation with invalid frequency."""
        # Arrange
        subscription = Subscription(
            payment_frequency="invalid",
            next_payment_date=date(2024, 1, 15),
        )

        # Act & Assert
        with pytest.raises(ValueError, match=ErrorMessages.UNKNOWN_PAYMENT_FREQUENCY):
            subscription.calculate_next_payment_date()


@pytest.mark.unit
class TestSubscriptionPrivateUtilityMethods:
    """Test Subscription model private utility methods."""

    def test_is_last_day_of_month_true_cases(self):
        """Test _is_last_day_of_month returns True for last days."""
        # Arrange
        subscription = Subscription()

        # Test cases: various last days of months
        test_dates = [
            date(2024, 1, 31),  # January
            date(2024, 2, 29),  # February (leap year)
            date(2023, 2, 28),  # February (non-leap year)
            date(2024, 4, 30),  # April
            date(2024, 6, 30),  # June
            date(2024, 12, 31),  # December
        ]

        # Act & Assert
        for test_date in test_dates:
            assert subscription._is_last_day_of_month(test_date) is True

    def test_is_last_day_of_month_false_cases(self):
        """Test _is_last_day_of_month returns False for non-last days."""
        # Arrange
        subscription = Subscription()

        # Test cases: various non-last days
        test_dates = [
            date(2024, 1, 30),  # Not last day of January
            date(2024, 2, 28),  # Not last day of February (leap year)
            date(2024, 4, 29),  # Not last day of April
            date(2024, 12, 30),  # Not last day of December
            date(2024, 6, 15),  # Middle of June
        ]

        # Act & Assert
        for test_date in test_dates:
            assert subscription._is_last_day_of_month(test_date) is False

    def test_add_months_basic_functionality(self):
        """Test _add_months basic functionality."""
        # Arrange
        subscription = Subscription()
        start_date = date(2024, 1, 15)

        # Act & Assert
        assert subscription._add_months(start_date, 1) == date(2024, 2, 15)
        assert subscription._add_months(start_date, 3) == date(2024, 4, 15)
        assert subscription._add_months(start_date, 12) == date(2025, 1, 15)

    def test_add_months_with_year_overflow(self):
        """Test _add_months handles year overflow correctly."""
        # Arrange
        subscription = Subscription()
        start_date = date(2024, 11, 15)

        # Act & Assert
        assert subscription._add_months(start_date, 2) == date(2025, 1, 15)
        assert subscription._add_months(start_date, 14) == date(2026, 1, 15)


@pytest.mark.unit
class TestSubscriptionEdgeCases:
    """Test Subscription model edge cases and boundary conditions."""

    def test_subscription_with_very_high_price(self):
        """Test subscription with very high price value."""
        # Arrange & Act
        subscription = Subscription(price=99999.99)

        # Assert
        subscription.validate_price()  # Should not raise
        assert subscription.price == 99999.99

    def test_subscription_with_very_low_price(self):
        """Test subscription with very low but valid price."""
        # Arrange & Act
        subscription = Subscription(price=0.01)

        # Assert
        subscription.validate_price()  # Should not raise
        assert subscription.price == 0.01

    def test_subscription_name_edge_cases(self):
        """Test subscription name with edge case values."""
        # Test very long name
        long_name = "A" * 100  # Maximum length
        subscription = Subscription(name=long_name)
        assert subscription.name == long_name

        # Test name with special characters
        special_name = "Netflix & Chill™ (Premium)"
        subscription = Subscription(name=special_name)
        assert subscription.name == special_name

    def test_currency_case_sensitivity(self):
        """Test currency validation normalizes to uppercase."""
        # Test that uppercase currencies work
        usd_sub = Subscription(currency="USD")
        jpy_sub = Subscription(currency="JPY")
        usd_sub.validate_currency()
        jpy_sub.validate_currency()
        assert usd_sub.currency == "USD"
        assert jpy_sub.currency == "JPY"

        # Test that lowercase currencies are normalized to uppercase
        lowercase_sub = Subscription(currency="usd")
        lowercase_sub.validate_currency()
        assert lowercase_sub.currency == "USD"  # Should be normalized to uppercase

        # Test that mixed case currencies are normalized to uppercase
        mixed_sub = Subscription(currency="jPy")
        mixed_sub.validate_currency()
        assert mixed_sub.currency == "JPY"  # Should be normalized to uppercase

        # Test that invalid currencies (even after normalization) still fail
        invalid_sub = Subscription(currency="eur")  # EUR is not supported
        with pytest.raises(ValueError, match="Unsupported currency"):
            invalid_sub.validate_currency()
