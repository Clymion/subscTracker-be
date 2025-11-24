from datetime import date
import pytest

from app.common import date_utils
from app.constants import PaymentFrequency


class TestDateUtils:
    # Tests for calculate_next_payment_date
    @pytest.mark.parametrize(
        "start_date, frequency, expected_date",
        [
            # Monthly
            (date(2024, 1, 15), PaymentFrequency.MONTHLY, date(2024, 2, 15)),
            (date(2024, 1, 31), PaymentFrequency.MONTHLY, date(2024, 2, 29)),  # Leap year
            (date(2023, 1, 31), PaymentFrequency.MONTHLY, date(2023, 2, 28)),
            (date(2024, 2, 29), PaymentFrequency.MONTHLY, date(2024, 3, 31)), # End of month sticks
            (date(2023, 3, 31), PaymentFrequency.MONTHLY, date(2023, 4, 30)),
            # Quarterly
            (date(2024, 1, 15), PaymentFrequency.QUARTERLY, date(2024, 4, 15)),
            (date(2023, 11, 30), PaymentFrequency.QUARTERLY, date(2024, 2, 29)),
            # Yearly
            (date(2024, 2, 29), PaymentFrequency.YEARLY, date(2025, 2, 28)),
            (date(2023, 2, 28), PaymentFrequency.YEARLY, date(2024, 2, 29)), # End of month sticks
            (date(2024, 1, 1), PaymentFrequency.YEARLY, date(2025, 1, 1)),
        ],
    )
    def test_calculate_next_payment_date(self, start_date, frequency, expected_date):
        assert (
            date_utils.calculate_next_payment_date(start_date, frequency)
            == expected_date
        )

    def test_calculate_next_payment_date_invalid_frequency(self):
        with pytest.raises(ValueError):
            date_utils.calculate_next_payment_date(date.today(), "invalid_frequency")

    # Tests for generate_payment_dates
    def test_generate_payment_dates_monthly(self):
        start_date = date(2023, 1, 15)
        end_date = date(2023, 4, 14)
        dates = date_utils.generate_payment_dates(
            start_date, end_date, PaymentFrequency.MONTHLY
        )
        assert dates == [
            date(2023, 1, 15),
            date(2023, 2, 15),
            date(2023, 3, 15),
        ]

    def test_generate_payment_dates_yearly(self):
        start_date = date(2020, 2, 29)
        end_date = date(2023, 2, 28)
        dates = date_utils.generate_payment_dates(
            start_date, end_date, PaymentFrequency.YEARLY
        )
        assert dates == [
            date(2020, 2, 29),
            date(2021, 2, 28),
            date(2022, 2, 28),
        ]

    def test_generate_payment_dates_no_payments_due(self):
        start_date = date(2023, 1, 15)
        end_date = date(2023, 1, 14)
        dates = date_utils.generate_payment_dates(
            start_date, end_date, PaymentFrequency.MONTHLY
        )
        assert dates == []

    def test_generate_payment_dates_start_date_after_end_date(self):
        start_date = date(2023, 2, 1)
        end_date = date(2023, 1, 1)
        dates = date_utils.generate_payment_dates(
            start_date, end_date, PaymentFrequency.MONTHLY
        )
        assert dates == []

    def test_end_of_month_preservation(self):
        """Tests that end-of-month dates are preserved across months."""
        # March 31 -> April 30
        d1 = date(2024, 3, 31)
        d2 = date_utils.calculate_next_payment_date(d1, PaymentFrequency.MONTHLY)
        assert d2 == date(2024, 4, 30)

        # April 30 -> May 31
        d3 = date_utils.calculate_next_payment_date(d2, PaymentFrequency.MONTHLY)
        assert d3 == date(2024, 5, 31)