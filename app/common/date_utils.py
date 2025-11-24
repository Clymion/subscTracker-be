"""
Date utility functions for handling payment date calculations.

This module provides helper functions for calculating next payment dates
and generating sequences of payment dates based on different frequencies,
handling complexities like month-ends and leap years.
"""

import calendar
from datetime import date

from app.constants import ErrorMessages, PaymentFrequency


def _is_last_day_of_month(check_date: date) -> bool:
    """Checks if a given date is the last day of its month."""
    last_day = calendar.monthrange(check_date.year, check_date.month)[1]
    return check_date.day == last_day


def _add_months(start_date: date, months: int) -> date:
    """
    Adds a specified number of months to a date with smart month-end handling.

    If the starting date is the last day of the month, the calculated date
    will also be the last day of the resulting month. Otherwise, it preserves
    the day, clamping to the last day if the resulting month is shorter.

    Args:
        start_date: The date to which months are added.
        months: The number of months to add.

    Returns:
        The new date after adding the months.
    """
    year = start_date.year
    month = start_date.month + months
    day = start_date.day

    # Adjust year and month for overflow
    while month > 12:
        year += 1
        month -= 12

    # Get the last day of the target month
    last_day_of_target_month = calendar.monthrange(year, month)[1]

    # If the start date was the last day of its month, the new date should also be
    if _is_last_day_of_month(start_date):
        day = last_day_of_target_month
    else:
        # Clamp day to the maximum possible for the target month
        day = min(day, last_day_of_target_month)

    return date(year, month, day)


def calculate_next_payment_date(from_date: date, frequency: str) -> date:
    """
    Calculates the next payment date based on a given frequency.

    Args:
        from_date: The starting date for calculation.
        frequency: The payment frequency (e.g., 'monthly', 'yearly').

    Returns:
        The calculated next payment date.

    Raises:
        ValueError: If the frequency is unknown.
    """
    if frequency == PaymentFrequency.MONTHLY:
        return _add_months(from_date, 1)
    if frequency == PaymentFrequency.QUARTERLY:
        return _add_months(from_date, 3)
    if frequency == PaymentFrequency.YEARLY:
        return _add_months(from_date, 12)

    msg = f"{ErrorMessages.UNKNOWN_PAYMENT_FREQUENCY}: {frequency}"
    raise ValueError(msg)


def generate_payment_dates(
    start_date: date, end_date: date, frequency: str
) -> list[date]:
    """
    Generates a list of payment dates between a start and end date.

    This function is inclusive of the start_date and exclusive of the end_date.
    It generates all payment dates that would have occurred up to, but not
    including, the end_date.

    Args:
        start_date: The initial date to start generating from.
        end_date: The date to generate payments up to (exclusive).
        frequency: The payment frequency.

    Returns:
        A list of payment dates.
    """
    dates = []
    current_date = start_date
    while current_date < end_date:
        dates.append(current_date)
        current_date = calculate_next_payment_date(current_date, frequency)
    return dates