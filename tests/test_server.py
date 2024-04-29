import os

import pytest
import requests

from pimsclient.server import EntryPath, PIMSServerError, truncate
from tests.conftest import set_mock_response
from tests.mock_responses import MockResponse


def test_exception_length_bound(requests_mock):
    """Recreates issue #289: very long error messages are relayed unbounded"""
    a_url = "http://a_url"
    set_mock_response(
        requests_mock,
        MockResponse(
            url=a_url,
            status_code=503,
            method="GET",
            text=str(os.urandom(4000)),
        ),
    )

    response = requests.get(a_url)
    with pytest.raises(PIMSServerError) as e:
        EntryPath.check_response(response)

    assert len(e.value.args[0]) == 300


def test_truncate():
    assert len(truncate("x" * 40, length=90)) == 40
    assert len(truncate("x" * 3000, length=90)) == 90

    with pytest.raises(ValueError):
        len(truncate("x" * 40, length=40))
