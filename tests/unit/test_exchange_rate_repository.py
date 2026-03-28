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


@pytest.mark.unit
@pytest.mark.database
def test_find_rates_by_base_currency(clean_db: Session):
    """
    Test finding the latest rates for all currency pairs based on a single base currency.
    """
    # Arrange
    # Ensure database is clean
    clean_db.query(ExchangeRate).delete()
    
    repo = ExchangeRateRepository(clean_db)
    rates = [
        # JPY -> USD (latest on the 26th)
        ExchangeRate(
            from_currency="JPY",
            to_currency="USD",
            date=date(2025, 9, 26),
            rate=0.0069,
            source="test",
        ),
        ExchangeRate(
            from_currency="JPY",
            to_currency="USD",
            date=date(2025, 9, 25),
            rate=0.00694,
            source="test",
        ),
        # EUR -> USD (latest on the 27th)
        ExchangeRate(
            from_currency="EUR",
            to_currency="USD",
            date=date(2025, 9, 27),
            rate=1.05,
            source="test",
        ),
        ExchangeRate(
            from_currency="EUR",
            to_currency="USD",
            date=date(2025, 9, 26),
            rate=1.04,
            source="test",
        ),
        # JPY -> EUR (should be ignored)
        ExchangeRate(
            from_currency="JPY",
            to_currency="EUR",
            date=date(2025, 9, 27),
            rate=0.0063,
            source="test",
        ),
        # JPY -> USD but after target date (should be ignored)
        ExchangeRate(
            from_currency="JPY",
            to_currency="USD",
            date=date(2025, 9, 28),
            rate=0.00685,
            source="test",
        ),
    ]
    clean_db.add_all(rates)
    clean_db.commit()

    # Act
    results = repo.find_rates_by_base_currency(
        target_date=date(2025, 9, 27),
        base_currency="USD",
    )

    # Assert
    assert len(results) == 2
    results_dict = {(r.from_currency, r.to_currency): r for r in results}

    # Check JPY -> USD rate
    assert ("JPY", "USD") in results_dict
    assert results_dict[("JPY", "USD")].rate == 0.0069
    assert results_dict[("JPY", "USD")].date == date(2025, 9, 26)

    # Check EUR -> USD rate
    assert ("EUR", "USD") in results_dict
    assert results_dict[("EUR", "USD")].rate == 1.05
    assert results_dict[("EUR", "USD")].date == date(2025, 9, 27)

