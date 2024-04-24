"""Fixtures shared between pytest modules"""
import pytest

from tests.mock_responses import (
    GET_DEIDENTIFY_RESPONSE,
    GET_IDENTITY_EXISTS_RESPONSE,
    GET_KEYFILE_RESPONSE,
    GET_PSEUDONYM_EXISTS_RESPONSE,
    GET_REIDENTIFY_RESPONSE,
)


def set_mock_response(requests_mock, response):
    """Register the given MockResponse with requests_mock"""
    requests_mock.register_uri(**response.as_dict())
    return response


@pytest.fixture
def mock_pims_responses(requests_mock):
    """Calls to several PIMS urls will return valid mocked responses"""
    set_mock_response(requests_mock, GET_KEYFILE_RESPONSE)
    set_mock_response(requests_mock, GET_DEIDENTIFY_RESPONSE)
    set_mock_response(requests_mock, GET_REIDENTIFY_RESPONSE)
    set_mock_response(requests_mock, GET_IDENTITY_EXISTS_RESPONSE)
    set_mock_response(requests_mock, GET_PSEUDONYM_EXISTS_RESPONSE)
