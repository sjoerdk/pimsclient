"""Fixtures shared between pytest modules"""

import pytest

from pimsclient.server import PIMSSession
from tests.factories import RequestsMock


@pytest.fixture()
def mock_pims_session(monkeypatch) -> PIMSSession:
    """PIMS session that does not hit any server and can return arbitrary responses"""
    mock = RequestsMock()
    session = PIMSSession(session=mock, base_url="https://testserver.test")
    return session


@pytest.fixture()
def mock_requests(monkeypatch):
    """Replace requests lib in pimsclient.server with a mock requests lib"""

    mock = RequestsMock
    monkeypatch.setattr("pimsclient.server.requests", mock)
    return mock
