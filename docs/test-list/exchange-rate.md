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

- **`test_find_rates_by_base_currency`**:
  - **Given**: Multiple rates for various currency pairs and dates exist in the database.
  - **When**: `find_rates_by_base_currency` is called with a specific base currency and target date.
  - **Then**: It returns a list containing only the most recent rate for each target currency, on or before the given date, for the specified base currency.

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

- **`test_get_rates_for_base_currency_found`**:
  - **Given**: The mocked repository returns a list of `ExchangeRate` objects.
  - **When**: `get_rates_for_base_currency` is called.
  - **Then**: It returns a dictionary of currency codes to rates.

- **`test_get_rates_for_base_currency_with_targets`**:
  - **Given**: The mocked repository returns a list of `ExchangeRate` objects.
  - **When**: `get_rates_for_base_currency` is called with a list of target currencies.
  - **Then**: It returns a dictionary containing only the specified target currencies.

- **`test_get_rates_for_base_currency_not_found`**:
  - **Given**: The mocked repository returns an empty list.
  - **When**: `get_rates_for_base_currency` is called.
  - **Then**: It raises a `ResourceNotFoundError`.

### Integration Tests - Exchange Rate API

File: `tests/integration/test_exchange_rate_api.py`

- **`test_get_rates_with_all_params_returns_200`**:
  - **Scenario**: A successful request combining `date`, `base_currency`, and `target_currencies` parameters.
  - **Expected**: HTTP 200 OK with correctly filtered rates based on all criteria.

- **`test_get_rates_with_base_currency_returns_200`**:
  - **Scenario**: A successful request with a specific base currency.
  - **Expected**: HTTP 200 OK with a dictionary of rates for that base currency.

- **`test_get_rates_with_target_currencies_returns_200`**:
  - **Scenario**: A successful request that filters for specific target currencies.
  - **Expected**: HTTP 200 OK with a dictionary containing only the requested target currencies.

- **`test_get_rates_with_specific_date_returns_200`**:
  - **Scenario**: A successful request for a specific historical date.
  - **Expected**: HTTP 200 OK with the rates from that date.

- **`test_get_rates_no_params_returns_defaults_200`**:
  - **Scenario**: A request with no query parameters.
  - **Expected**: HTTP 200 OK with default behavior (base=USD, latest date).

- **`test_get_rates_invalid_date_format_returns_400`**:
  - **Scenario**: A request with a malformed `date` parameter.
  - **Expected**: HTTP 400 Bad Request with a relevant error message.

- **`test_get_rates_invalid_currency_code_returns_400`**:
  - **Scenario**: A request with an invalid `base_currency` or `target_currencies` code.
  - **Expected**: HTTP 400 Bad Request with a relevant error message.

- **`test_get_rates_not_found_returns_404`**:
  - **Scenario**: A request for a base currency with no available rates.
  - **Expected**: HTTP 404 Not Found.

- **`test_get_rates_no_auth_token_returns_401`**:
  - **Scenario**: An unauthenticated request (missing Authorization header) to the endpoint.
  - **Expected**: HTTP 401 Unauthorized with a JSON error message.
