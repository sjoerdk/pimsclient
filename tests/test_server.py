#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pytest

from pimsclient.server import PIMSSession, PIMSServerException
from tests.factories import UserFactory, RequestsMock, RequestsMockResponseExamples


@pytest.mark.parametrize(
    "mock_response",
    [
        RequestsMockResponseExamples.KEYFILE_DOES_NOT_EXIST,
        RequestsMockResponseExamples.ACTION_REFUSED_INSUFFICIENT_RIGHTS,
        RequestsMockResponseExamples.REQUESTED_RESOURCE_DOES_NOT_SUPPORT,
        RequestsMockResponseExamples.UKNOWN_URL,
        RequestsMockResponseExamples.UNAUTHORIZED,
    ],
)
def test_swagger_error_responses(mock_pims_session, mock_response):
    """Swagger API error responses should be caught in proper exceptions
    """
    mock_pims_session.session.set_response_tuple(mock_response)
    with pytest.raises(PIMSServerException):
        mock_pims_session.get(
            "a_url"
        )  # actual url does not matter as mock response is returned by requests

    with pytest.raises(PIMSServerException):
        mock_pims_session.post("a_url", params={})
