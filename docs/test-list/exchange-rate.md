# Test List: Exchange Rate API

## Feature Description

This feature provides a RESTful API endpoint to retrieve currency exchange rates. It's designed to find the most recent available rate on or before a specified date for a given currency pair.

## Related Requirements

- **REQ-ER-01**: The system must provide an API endpoint `GET /api/v1/exchange-rates` to fetch exchange rates.
- **REQ-ER-02**: The API must accept `date`, `from_currency`, and `to_currency` as query parameters.
- **REQ-ER-03**: If a rate for the exact date is not available, the system shall return the most recent rate prior to that date.
- **REQ-ER-04**: If no date is provided, the system should default to the current server date.
- **REQ-ER-05**: The API must return a 404 Not Found error if no rate can be found for the given criteria.
- **REQ-ER-06**: The API must return a 400 Bad Request error for missing currency parameters or invalid date formats.

---

## Test Categories

### Unit Tests - ExchangeRateRepository

File: `tests/unit/test_exchange_rate_repository.py`

- **`test_find_rate_by_date_found`**: 
  - **Given**: An exact rate for the target date exists in the database.
  - **When**: `find_rate_by_date` is called with that date.
  - **Then**: It returns the correct `ExchangeRate` object for that date.

- **`test_find_rate_by_date_fallback`**:
  - **Given**: No rate exists for the target date, but rates exist for previous dates.
  - **When**: `find_rate_by_date` is called.
  - **Then**: It returns the `ExchangeRate` object for the most recent date *before* the target date.

- **`test_find_rate_by_date_not_found`**:
  - **Given**: No rates exist on or before the target date for the currency pair.
  - **When**: `find_rate_by_date` is called.
  - **Then**: It returns `None`.

- **`test_find_rate_by_date_wrong_currency`**:
  - **Given**: Rates exist, but not for the requested currency pair.
  - **When**: `find_rate_by_date` is called.
  - **Then**: It returns `None`.

### Unit Tests - ExchangeRateService

File: `tests/unit/test_exchange_rate_service.py`

- **`test_get_exchange_rate_found`**:
  - **Given**: The mocked repository will return a valid `ExchangeRate` object.
  - **When**: The service's `get_exchange_rate` method is called.
  - **Then**: The service returns the same `ExchangeRate` object provided by the repository.

- **`test_get_exchange_rate_not_found_raises_error`**:
  - **Given**: The mocked repository will return `None`.
  - **When**: The service's `get_exchange_rate` method is called.
  - **Then**: The service raises a `ResourceNotFoundError`.

### Integration Tests - Exchange Rate API

File: `tests/integration/test_exchange_rate_api.py`

- **`test_get_rate_with_exact_date_returns_200`**:
  - **Scenario**: A successful request for a date with an exact rate match.
  - **Expected**: HTTP 200 OK with the correct rate in the response body.

- **`test_get_rate_with_fallback_date_returns_200`**:
  - **Scenario**: A successful request for a date that has no exact match, triggering the fallback logic.
  - **Expected**: HTTP 200 OK with the most recent prior rate.

- **`test_get_rate_without_date_returns_most_recent_200`**:
  - **Scenario**: A request where the `date` parameter is omitted.
  - **Expected**: HTTP 200 OK with the most recent available rate for the currency pair.

- **`test_get_rate_not_found_returns_404`**:
  - **Scenario**: A request for a currency pair and date for which no rate exists (not even in the past).
  - **Expected**: HTTP 404 Not Found with a corresponding error message.

- **`test_get_rate_missing_param_returns_400`**:
  - **Scenario**: A request that is missing one of the required currency parameters (`from_currency` or `to_currency`).
  - **Expected**: HTTP 400 Bad Request with a message indicating missing parameters.

- **`test_get_rate_invalid_date_format_returns_400`**:
  - **Scenario**: A request with a malformed `date` parameter (e.g., `DD-MM-YYYY`).
  - **Expected**: HTTP 400 Bad Request with a message indicating an invalid date format.
