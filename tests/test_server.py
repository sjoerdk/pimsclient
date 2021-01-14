import pytest

from pimsclient.server import PIMSServerException, PIMSServer
from tests.factories import RequestsMockResponseExamples


@pytest.mark.parametrize(
    "mock_response",
    [
        RequestsMockResponseExamples.KEYFILE_DOES_NOT_EXIST,
        RequestsMockResponseExamples.ACTION_REFUSED_INSUFFICIENT_RIGHTS,
        RequestsMockResponseExamples.REQUESTED_RESOURCE_DOES_NOT_SUPPORT,
        RequestsMockResponseExamples.UKNOWN_URL,
        RequestsMockResponseExamples.UNAUTHORIZED,
        RequestsMockResponseExamples.INVALID_API_REQUEST,
        RequestsMockResponseExamples.UNKNOWN_ERROR,
    ],
)
def test_swagger_error_responses(mock_pims_session, mock_response):
    """Swagger API error responses should be caught in proper exceptions"""
    mock_pims_session.session.set_response_tuple(mock_response)
    with pytest.raises(PIMSServerException):
        mock_pims_session.get(
            "a_url"
        )  # actual url does not matter as mock response is returned by requests

    with pytest.raises(PIMSServerException):
        mock_pims_session.post("a_url", params={})


def test_mock_response_session(mock_requests, monkeypatch):
    server = PIMSServer(url="Test")

    with pytest.raises(PIMSServerException):
        # no password defined, should raise exception
        server.get_session()

    # this should work though
    server.get_session(user="test", password="password")

    # and this
    monkeypatch.setenv("PIMS_CLIENT_USER", "TestUser")
    monkeypatch.setenv("PIMS_CLIENT_PASSWORD", "TestPass")
    server.get_session()
