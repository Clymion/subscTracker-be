from unittest.mock import MagicMock

import pytest


@pytest.fixture
def mock_session():
    session = MagicMock()
    query = session.query.return_value
    query.filter.return_value = query
    query.join.return_value = query
    query.order_by.return_value = query
    query.limit.return_value = query
    query.offset.return_value = query
    return session
