"""
Unit tests for API response common utilities.

Pure unit tests that do not depend on Flask application context, environment variables,
or external configurations. Tests focus on response formatting and pagination logic.
"""

import pytest

from app.common.response_utils import (
    PaginationError,
    paginate_query_params,
    pagination_metadata,
    success_response,
)
from app.constants import ErrorMessages


class TestSuccessResponse:
    """Test success_response utility function."""

    def test_success_response_with_data(self):
        """Test success response formatting with data payload."""
        # Arrange
        test_data = {"message": "Hello, world!", "status": "ok"}

        # Act
        response, status_code = success_response(test_data)

        # Assert
        assert status_code == 200
        assert "data" in response
        assert "meta" in response
        assert response["data"] == test_data
        assert response["meta"] == {}

    def test_success_response_with_empty_data(self):
        """Test success response formatting with empty data."""
        # Arrange
        empty_data = {}

        # Act
        response, status_code = success_response(empty_data)

        # Assert
        assert status_code == 200
        assert response["data"] == {}
        assert response["meta"] == {}

    def test_success_response_with_meta(self):
        """Test success response formatting with metadata."""
        # Arrange
        test_data = {"items": ["item1", "item2"]}
        test_meta = {"total": 2, "page": 1}

        # Act
        response, status_code = success_response(test_data, test_meta)

        # Assert
        assert status_code == 200
        assert response["data"] == test_data
        assert response["meta"] == test_meta

    def test_success_response_with_complex_data(self):
        """Test success response with complex nested data."""
        # Arrange
        complex_data = {
            "users": [
                {"id": 1, "name": "User 1", "roles": ["admin", "user"]},
                {"id": 2, "name": "User 2", "roles": ["user"]},
            ],
            "summary": {"total_users": 2, "active_users": 2},
        }
        meta_data = {
            "pagination": {"page": 1, "per_page": 10, "total": 2},
            "filters": {"active": True},
        }

        # Act
        response, status_code = success_response(complex_data, meta_data)

        # Assert
        assert status_code == 200
        assert response["data"] == complex_data
        assert response["meta"] == meta_data

    def test_success_response_preserves_data_types(self):
        """Test that success response preserves various data types."""
        # Arrange
        typed_data = {
            "string": "text",
            "integer": 42,
            "float": 3.14,
            "boolean": True,
            "list": [1, 2, 3],
            "dict": {"nested": "value"},
            "none": None,
        }

        # Act
        response, status_code = success_response(typed_data)

        # Assert
        assert status_code == 200
        assert response["data"]["string"] == "text"
        assert response["data"]["integer"] == 42
        assert response["data"]["float"] == 3.14
        assert response["data"]["boolean"] is True
        assert response["data"]["list"] == [1, 2, 3]
        assert response["data"]["dict"] == {"nested": "value"}
        assert response["data"]["none"] is None


class TestPaginateQueryParams:
    """Test paginate_query_params utility function."""

    def test_paginate_with_default_values(self):
        """Test pagination with no parameters (should use defaults)."""
        # Arrange
        empty_args = {}

        # Act
        limit, offset = paginate_query_params(empty_args)

        # Assert
        assert limit == 20  # default limit
        assert offset == 0  # default offset

    def test_paginate_with_valid_parameters(self):
        """Test pagination with valid limit and offset."""
        # Arrange
        args = {"limit": "10", "offset": "20"}

        # Act
        limit, offset = paginate_query_params(args)

        # Assert
        assert limit == 10
        assert offset == 20

    def test_paginate_with_custom_defaults(self):
        """Test pagination with custom default values."""
        # Arrange
        args = {}

        # Act
        limit, offset = paginate_query_params(args, default_limit=50, max_limit=200)

        # Assert
        assert limit == 50
        assert offset == 0

    def test_paginate_with_only_limit(self):
        """Test pagination with only limit parameter."""
        # Arrange
        args = {"limit": "15"}

        # Act
        limit, offset = paginate_query_params(args)

        # Assert
        assert limit == 15
        assert offset == 0  # default offset

    def test_paginate_with_only_offset(self):
        """Test pagination with only offset parameter."""
        # Arrange
        args = {"offset": "30"}

        # Act
        limit, offset = paginate_query_params(args)

        # Assert
        assert limit == 20  # default limit
        assert offset == 30

    def test_paginate_with_zero_values(self):
        """Test pagination with zero values."""
        # Arrange
        args = {"limit": "0", "offset": "0"}

        # Act
        limit, offset = paginate_query_params(args)

        # Assert
        assert limit == 0
        assert offset == 0

    def test_paginate_with_large_values(self):
        """Test pagination with large but valid values."""
        # Arrange
        args = {"limit": "100", "offset": "1000"}

        # Act
        limit, offset = paginate_query_params(args, max_limit=150)

        # Assert
        assert limit == 100
        assert offset == 1000


class TestPaginateQueryParamsErrorHandling:
    """Test error handling in paginate_query_params function."""

    def test_paginate_with_invalid_limit_string(self):
        """Test pagination error with non-numeric limit."""
        # Arrange
        args = {"limit": "abc", "offset": "5"}

        # Act & Assert
        with pytest.raises(
            PaginationError, match=ErrorMessages.PAGINATION_LIMIT_OFFSET_NOT_INTEGER
        ):
            paginate_query_params(args)

    def test_paginate_with_invalid_offset_string(self):
        """Test pagination error with non-numeric offset."""
        # Arrange
        args = {"limit": "10", "offset": "xyz"}

        # Act & Assert
        with pytest.raises(
            PaginationError, match=ErrorMessages.PAGINATION_LIMIT_OFFSET_NOT_INTEGER
        ):
            paginate_query_params(args)

    def test_paginate_with_negative_limit(self):
        """Test pagination error with negative limit."""
        # Arrange
        args = {"limit": "-5", "offset": "0"}

        # Act & Assert
        with pytest.raises(PaginationError):
            paginate_query_params(args)

    def test_paginate_with_limit_exceeding_max(self):
        """Test pagination error with limit exceeding maximum."""
        # Arrange
        args = {"limit": "150", "offset": "0"}

        # Act & Assert
        with pytest.raises(PaginationError):
            paginate_query_params(args, max_limit=100)

    def test_paginate_with_negative_offset(self):
        """Test pagination error with negative offset."""
        # Arrange
        args = {"limit": "10", "offset": "-1"}

        # Act & Assert
        with pytest.raises(
            PaginationError, match=ErrorMessages.PAGINATION_OFFSET_NEGATIVE
        ):
            paginate_query_params(args)

    def test_paginate_with_float_values(self):
        """Test pagination error with float values."""
        # Arrange
        args = {"limit": "10.5", "offset": "5.5"}

        # Act & Assert
        with pytest.raises(PaginationError):
            paginate_query_params(args)

    def test_paginate_with_empty_string_values(self):
        """Test pagination error with empty string values."""
        # Arrange
        args = {"limit": "", "offset": ""}

        # Act & Assert
        with pytest.raises(PaginationError):
            paginate_query_params(args)


class TestPaginationMetadata:
    """Test pagination_metadata utility function."""

    def test_pagination_metadata_basic(self):
        """Test basic pagination metadata generation."""
        # Arrange
        limit = 10
        offset = 0
        total = 100
        base_url = "https://api.example.com/items"
        args = {"limit": "10", "offset": "0"}

        # Act
        meta = pagination_metadata(limit, offset, total, base_url, args)

        # Assert
        assert meta["total"] == 100
        assert meta["limit"] == 10
        assert meta["offset"] == 0
        assert meta["next"] is not None
        assert meta["previous"] is None

    def test_pagination_metadata_with_next_page(self):
        """Test pagination metadata when there is a next page."""
        # Arrange
        limit = 10
        offset = 20
        total = 100
        base_url = "https://api.example.com/items"
        args = {"limit": "10", "offset": "20"}

        # Act
        meta = pagination_metadata(limit, offset, total, base_url, args)

        # Assert
        assert "next" in meta
        assert meta["next"] is not None
        assert "offset=30" in meta["next"]
        assert "limit=10" in meta["next"]

    def test_pagination_metadata_with_previous_page(self):
        """Test pagination metadata when there is a previous page."""
        # Arrange
        limit = 10
        offset = 20
        total = 100
        base_url = "https://api.example.com/items"
        args = {"limit": "10", "offset": "20"}

        # Act
        meta = pagination_metadata(limit, offset, total, base_url, args)

        # Assert
        assert "previous" in meta
        assert meta["previous"] is not None
        assert "offset=10" in meta["previous"]
        assert "limit=10" in meta["previous"]

    def test_pagination_metadata_last_page(self):
        """Test pagination metadata on the last page."""
        # Arrange
        limit = 10
        offset = 90
        total = 100
        base_url = "https://api.example.com/items"
        args = {"limit": "10", "offset": "90"}

        # Act
        meta = pagination_metadata(limit, offset, total, base_url, args)

        # Assert
        assert meta["next"] is None  # No next page
        assert meta["previous"] is not None  # Has previous page

    def test_pagination_metadata_first_page(self):
        """Test pagination metadata on the first page."""
        # Arrange
        limit = 10
        offset = 0
        total = 100
        base_url = "https://api.example.com/items"
        args = {"limit": "10", "offset": "0"}

        # Act
        meta = pagination_metadata(limit, offset, total, base_url, args)

        # Assert
        assert meta["previous"] is None  # No previous page
        assert meta["next"] is not None  # Has next page

    def test_pagination_metadata_single_page(self):
        """Test pagination metadata when all data fits in one page."""
        # Arrange
        limit = 50
        offset = 0
        total = 25
        base_url = "https://api.example.com/items"
        args = {"limit": "50", "offset": "0"}

        # Act
        meta = pagination_metadata(limit, offset, total, base_url, args)

        # Assert
        assert meta["next"] is None
        assert meta["previous"] is None

    def test_pagination_metadata_with_additional_query_params(self):
        """Test pagination metadata preserves other query parameters."""
        # Arrange
        limit = 10
        offset = 10
        total = 100
        base_url = "https://api.example.com/items"
        args = {
            "limit": "10",
            "offset": "10",
            "search": "test",
            "category": "books",
            "sort": "name",
        }

        # Act
        meta = pagination_metadata(limit, offset, total, base_url, args)

        # Assert
        assert "search=test" in meta["next"]
        assert "category=books" in meta["next"]
        assert "sort=name" in meta["next"]
        assert "search=test" in meta["previous"]
        assert "category=books" in meta["previous"]
        assert "sort=name" in meta["previous"]

    def test_pagination_metadata_edge_cases(self):
        """Test pagination metadata with edge cases."""
        # Test with offset exactly at the boundary
        limit = 10
        offset = 10
        total = 20
        base_url = "https://api.example.com/items"
        args = {"limit": "10", "offset": "10"}

        meta = pagination_metadata(limit, offset, total, base_url, args)

        assert (
            meta["next"] is None
        )  # No next page (offset 10 + limit 10 = 20, equals total)
        assert meta["previous"] is not None


class TestPaginationErrorHandling:
    """Test PaginationError exception handling."""

    def test_pagination_error_inheritance(self):
        """Test that PaginationError inherits from ValueError."""
        # Act & Assert
        assert issubclass(PaginationError, ValueError)

    def test_pagination_error_can_be_raised(self):
        """Test that PaginationError can be raised and caught."""
        # Arrange
        error_message = "Test pagination error"

        # Act & Assert
        with pytest.raises(PaginationError, match=error_message):
            raise PaginationError(error_message)

    def test_pagination_error_can_be_caught_as_value_error(self):
        """Test that PaginationError can be caught as ValueError."""
        # Arrange
        error_message = "Test pagination error"

        # Act & Assert
        with pytest.raises(ValueError, match=error_message):
            raise PaginationError(error_message)


class TestResponseUtilsIntegration:
    """Test integration between different response utility functions."""

    def test_success_response_with_pagination_metadata(self):
        """Test integrating success response with pagination metadata."""
        # Arrange
        data = {"items": [{"id": 1}, {"id": 2}, {"id": 3}]}
        limit = 10
        offset = 0
        total = 3
        base_url = "https://api.example.com/items"
        args = {"limit": "10", "offset": "0"}

        # Generate pagination metadata
        pagination_meta = pagination_metadata(limit, offset, total, base_url, args)

        # Act
        response, status_code = success_response(data, {"pagination": pagination_meta})

        # Assert
        assert status_code == 200
        assert response["data"] == data
        assert "pagination" in response["meta"]
        assert response["meta"]["pagination"]["total"] == 3
        assert response["meta"]["pagination"]["limit"] == 10
        assert response["meta"]["pagination"]["offset"] == 0

    def test_complete_pagination_workflow(self):
        """Test complete pagination workflow from query params to response."""
        # Arrange
        query_args = {"limit": "5", "offset": "10", "search": "test"}
        base_url = "https://api.example.com/search"
        mock_data = [{"id": i} for i in range(11, 16)]  # 5 items
        total_items = 50

        # Act
        # 1. Parse query parameters
        limit, offset = paginate_query_params(query_args)

        # 2. Generate pagination metadata
        pagination_meta = pagination_metadata(
            limit, offset, total_items, base_url, query_args
        )

        # 3. Create success response
        response_data = {"items": mock_data}
        response, status_code = success_response(
            response_data, {"pagination": pagination_meta}
        )

        # Assert
        assert status_code == 200
        assert len(response["data"]["items"]) == 5
        assert response["meta"]["pagination"]["total"] == 50
        assert response["meta"]["pagination"]["limit"] == 5
        assert response["meta"]["pagination"]["offset"] == 10
        assert response["meta"]["pagination"]["next"] is not None
        assert response["meta"]["pagination"]["previous"] is not None
        assert "search=test" in response["meta"]["pagination"]["next"]
