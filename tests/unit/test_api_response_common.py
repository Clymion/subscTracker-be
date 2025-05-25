import pytest
from flask import Flask, Request
from werkzeug.exceptions import BadRequest

from app.common.response_utils import (
    PaginationError,
    paginate_query_params,
    pagination_metadata,
    success_response,
)


@pytest.fixture
def app() -> Flask:
    """Create a Flask app instance with test routes for response utilities."""
    app = Flask(__name__)

    @app.route("/test-success")
    def test_success() -> tuple[dict, int]:
        data = {"message": "Hello, world!"}
        return success_response(data)

    @app.route("/test-pagination")
    def test_pagination() -> tuple[dict, int]:
        try:
            limit, offset = paginate_query_params(Request.args)
        except PaginationError as e:
            raise BadRequest(str(e))
        # Simulate total count for metadata
        total = 100
        meta = pagination_metadata(limit, offset, total, Request.base_url, Request.args)
        return success_response({"items": [], "meta": meta})

    return app


def test_success_response_formatting(app: Flask) -> None:
    client = app.test_client()
    response = client.get("/test-success")
    json_data = response.get_json()
    assert response.status_code == 200
    assert "data" in json_data
    assert json_data["data"] == {"message": "Hello, world!"}
    assert "meta" in json_data
    assert json_data["meta"] == {}


def test_success_response_empty_data(app: Flask) -> None:
    client = app.test_client()

    @app.route("/test-empty")
    def test_empty() -> tuple[dict, int]:
        return success_response({})

    response = client.get("/test-empty")
    json_data = response.get_json()
    assert response.status_code == 200
    assert json_data["data"] == {}
    assert "meta" in json_data


def test_paginate_query_params_defaults(app: Flask) -> None:
    with app.test_request_context("/test-pagination"):
        limit, offset = paginate_query_params({})
        assert limit == 20  # default limit
        assert offset == 0  # default offset


def test_paginate_query_params_valid(app: Flask) -> None:
    with app.test_request_context("/test-pagination?limit=10&offset=5"):
        limit, offset = paginate_query_params({"limit": "10", "offset": "5"})
        assert limit == 10
        assert offset == 5


def test_paginate_query_params_invalid(app: Flask) -> None:
    with app.test_request_context("/test-pagination?limit=abc&offset=-1"):
        with pytest.raises(PaginationError):
            paginate_query_params({"limit": "abc", "offset": "-1"})


def test_pagination_metadata_correct() -> None:
    limit = 10
    offset = 20
    total = 100
    base_url = "http://localhost/test-pagination"
    args = {"limit": "10", "offset": "20"}
    meta = pagination_metadata(limit, offset, total, base_url, args)
    assert meta["total"] == total
    assert meta["limit"] == limit
    assert meta["offset"] == offset
    assert "next" in meta
    assert "previous" in meta


def test_pagination_metadata_no_next() -> None:
    limit = 10
    offset = 90
    total = 100
    base_url = "http://localhost/test-pagination"
    args = {"limit": "10", "offset": "90"}
    meta = pagination_metadata(limit, offset, total, base_url, args)
    assert meta["next"] is None


def test_pagination_metadata_no_previous() -> None:
    limit = 10
    offset = 0
    total = 100
    base_url = "http://localhost/test-pagination"
    args = {"limit": "10", "offset": "0"}
    meta = pagination_metadata(limit, offset, total, base_url, args)
    assert meta["previous"] is None
