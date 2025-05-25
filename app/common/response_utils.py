from urllib.parse import urlencode

from app.constants import ErrorMessages


class PaginationError(ValueError):
    """Exception raised for errors in pagination parameters."""

    pass


def success_response(data: dict, meta: dict | None = None) -> tuple[dict, int]:
    """
    Format a standardized success response.

    Args:
        data: The main data payload as a dictionary.
        meta: Optional metadata dictionary.

    Returns:
        A tuple containing the response dictionary and HTTP status code 200.

    """
    if meta is None:
        meta = {}
    response = {
        "data": data,
        "meta": meta,
    }
    return response, 200


def paginate_query_params(
    args: dict[str, str],
    default_limit: int = 20,
    max_limit: int = 100,
) -> tuple[int, int]:
    """
    Parse and validate pagination query parameters from request arguments.

    Args:
        args: Dictionary of query parameters.
        default_limit: Default limit if not specified.
        max_limit: Maximum allowed limit.

    Returns:
        A tuple of (limit, offset) as integers.

    Raises:
        PaginationError: If parameters are invalid.

    """
    limit_str = args.get("limit")
    offset_str = args.get("offset")

    try:
        limit = int(limit_str) if limit_str is not None else default_limit
        offset = int(offset_str) if offset_str is not None else 0
    except ValueError as e:
        raise PaginationError(ErrorMessages.PAGINATION_LIMIT_OFFSET_NOT_INTEGER) from e

    if limit < 0 or limit > max_limit:
        raise PaginationError(
            ErrorMessages.PAGINATION_LIMIT_OUT_OF_RANGE.format(max_limit=max_limit),
        )
    if offset < 0:
        raise PaginationError(ErrorMessages.PAGINATION_OFFSET_NEGATIVE)

    return limit, offset


def pagination_metadata(
    limit: int,
    offset: int,
    total: int,
    base_url: str,
    args: dict[str, str],
) -> dict[str, str | int | None]:
    """
    Generate pagination metadata for response.

    Args:
        limit: Number of items per page.
        offset: Current offset.
        total: Total number of items.
        base_url: Base URL for constructing links.
        args: Original query parameters.

    Returns:
        A dictionary with pagination metadata including total, limit, offset,
        and URLs for next and previous pages if applicable.

    """
    meta: dict[str, str | int | None] = {
        "total": total,
        "limit": limit,
        "offset": offset,
        "next": None,
        "previous": None,
    }

    def build_url(new_offset: int) -> str:
        params = args.copy()
        params["limit"] = str(limit)
        params["offset"] = str(new_offset)
        return f"{base_url}?{urlencode(params)}"

    next_offset = offset + limit
    if next_offset < total:
        meta["next"] = build_url(next_offset)

    prev_offset = offset - limit
    if prev_offset >= 0:
        meta["previous"] = build_url(prev_offset)
    elif offset > 0:
        meta["previous"] = build_url(0)

    return meta
