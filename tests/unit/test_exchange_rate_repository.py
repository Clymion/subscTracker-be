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
    repo = ExchangeRateRepository(clean_db)
    rates = [
        # USD -> JPY (latest on the 26th)
        ExchangeRate(
            from_currency="USD",
            to_currency="JPY",
            date=date(2025, 9, 26),
            rate=145.0,
            source="test",
        ),
        ExchangeRate(
            from_currency="USD",
            to_currency="JPY",
            date=date(2025, 9, 25),
            rate=144.0,
            source="test",
        ),
        # USD -> EUR (latest on the 27th)
        ExchangeRate(
            from_currency="USD",
            to_currency="EUR",
            date=date(2025, 9, 27),
            rate=0.95,
            source="test",
        ),
        ExchangeRate(
            from_currency="USD",
            to_currency="EUR",
            date=date(2025, 9, 26),
            rate=0.94,
            source="test",
        ),
        # EUR -> JPY (should be ignored)
        ExchangeRate(
            from_currency="EUR",
            to_currency="JPY",
            date=date(2025, 9, 27),
            rate=160.0,
            source="test",
        ),
        # USD -> JPY but after target date (should be ignored)
        ExchangeRate(
            from_currency="USD",
            to_currency="JPY",
            date=date(2025, 9, 28),
            rate=146.0,
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

    # Check USD -> JPY rate
    assert ("USD", "JPY") in results_dict
    assert results_dict[("USD", "JPY")].rate == 145.0
    assert results_dict[("USD", "JPY")].date == date(2025, 9, 26)

    # Check USD -> EUR rate
    assert ("USD", "EUR") in results_dict
    assert results_dict[("USD", "EUR")].rate == 0.95
    assert results_dict[("USD", "EUR")].date == date(2025, 9, 27)

