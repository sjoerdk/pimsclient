"""Fixtures shared between pytest modules
"""

import pytest

from pimsclient.server import PIMSSession
from tests.factories import RequestsMock


@pytest.fixture()
def mock_pims_session(monkeypatch):
    """PIMS session that does not hit any server and can return arbitrary responses

    Returns
    -------
    PIMSSession

    """
    mock = RequestsMock()
    session = PIMSSession(session=mock, base_url="https://testserver.test")
    return session


