"""
Unit tests for the ExchangeRateRepository.
"""
from datetime import date

import pytest
from sqlalchemy.orm import Session

from app.models.exchange_rate import ExchangeRate
from app.repositories.exchange_rate_repository import ExchangeRateRepository


@pytest.mark.unit
@pytest.mark.database
def test_find_rate_by_date_found(clean_db: Session):
    """
    Test finding an exchange rate when an exact match for the date exists.
    """
    # Arrange
    repo = ExchangeRateRepository(clean_db)
    rate1 = ExchangeRate(
        from_currency="USD",
        to_currency="JPY",
        date=date(2025, 9, 27),
        rate=145.5,
        source="test",
    )
    rate2 = ExchangeRate(
        from_currency="USD",
        to_currency="JPY",
        date=date(2025, 9, 26),
        rate=145.0,
        source="test",
    )
    clean_db.add_all([rate1, rate2])
    clean_db.commit()

    # Act
    result = repo.find_rate_by_date(
        target_date=date(2025, 9, 27),
        from_currency="USD",
        to_currency="JPY",
    )

    # Assert
    assert result is not None
    assert result.rate == 145.5
    assert result.date == date(2025, 9, 27)


@pytest.mark.unit
@pytest.mark.database
def test_find_rate_by_date_fallback(clean_db: Session):
    """
    Test the fallback logic to find the most recent rate before the target date.
    """
    # Arrange
    repo = ExchangeRateRepository(clean_db)
    rate1 = ExchangeRate(
        from_currency="USD",
        to_currency="JPY",
        date=date(2025, 9, 25),
        rate=144.5,
        source="test",
    )
    rate2 = ExchangeRate(
        from_currency="USD",
        to_currency="JPY",
        date=date(2025, 9, 26),
        rate=145.0,
        source="test",
    )
    clean_db.add_all([rate1, rate2])
    clean_db.commit()

    # Act
    result = repo.find_rate_by_date(
        target_date=date(2025, 9, 27),
        from_currency="USD",
        to_currency="JPY",
    )

    # Assert
    assert result is not None
    assert result.rate == 145.0
    assert result.date == date(2025, 9, 26)


@pytest.mark.unit
@pytest.mark.database
def test_find_rate_by_date_not_found(clean_db: Session):
    """
    Test that None is returned when no rate is found on or before the date.
    """
    # Arrange
    repo = ExchangeRateRepository(clean_db)
    rate1 = ExchangeRate(
        from_currency="USD",
        to_currency="JPY",
        date=date(2025, 9, 28),
        rate=146.0,
        source="test",
    )
    clean_db.add(rate1)
    clean_db.commit()

    # Act
    result = repo.find_rate_by_date(
        target_date=date(2025, 9, 27),
        from_currency="USD",
        to_currency="JPY",
    )

    # Assert
    assert result is None


@pytest.mark.unit
@pytest.mark.database
def test_find_rate_by_date_wrong_currency(clean_db: Session):
    """
    Test that None is returned when the currency pair does not match.
    """
    # Arrange
    repo = ExchangeRateRepository(clean_db)
    rate1 = ExchangeRate(
        from_currency="EUR",
        to_currency="JPY",
        date=date(2025, 9, 27),
        rate=160.0,
        source="test",
    )
    clean_db.add(rate1)
    clean_db.commit()

    # Act
    result = repo.find_rate_by_date(
        target_date=date(2025, 9, 27),
        from_currency="USD",
        to_currency="JPY",
    )

    # Assert
    assert result is None
