"""Interaction with a webserver running the PIMS web API. This handles the actual
http traffic on one side, and communicates using parsed objects and exceptions on the
other.

Notes
-----
Server methods:
* Call http directly and interpret the response, raising exceptions as needed
* Return parsed API Response objects, found in swagger_models.py
* Take basic parameters as input, int, str, etc. API request objects are always
  constructed inside the methods, so that users do not need to know about them to
  call a response. API response object as return value is OK because they are mostly
  dicts anyway, and you can inspect and take what you need from them

"""
import json
from collections import defaultdict
from typing import Dict, List, Type, Union

import pydantic
import requests

from pimsclient.core import Identifier, Pseudonym
from pimsclient.exceptions import PIMSError
from pimsclient.logs import get_module_logger
from pimsclient.autogen.swagger_models_v0 import (
    FileOptions,
    IdentitiesRequest,
    KeyfileResponse,
    PseudonymIdentityResponse,
    PseudonymisationAction,
    PseudonymisationRequest,
    PseudonymisationResults,
    PseudonymsReidentificationRequest,
    PseudonymsRequest,
    ReidentificationRequest,
    ReidentificationResult,
)
from pimsclient.swagger import MyJsonDataHeader

logger = get_module_logger("server")


class PIMSServer:
    """A PIMS API server at a certain url

    Notes
    -----
    Responsibilities of the server class:
    * Expose API entrypoints as classes and methods
    * Entrypoints always return parsed python objects, never json or dicts. Server
      Translates, (de)serializes API responses.
    * Server checks https responses and raises exceptions if needed
    * From a client perspective, all https traffic hidden. Server handles this.
    """

    def __init__(self, url: str):
        """

        Parameters
        ----------
        url
            API entrypoint. prepended to all entrypoint paths.
            Like https://hostname.com/api
        """
        self.url = url
        self.keyfiles: Keyfiles = Keyfiles(base_url=url)
        self.identities: Identities = Identities(base_url=url)
        self.pseudonyms: Pseudonyms = Pseudonyms(base_url=url)
        self.files: Files = Files(base_url=url)

        # maximum number of pseudonyms/identities to request at once
        self.max_bulk_size: int = 20000


def truncate(text, length=300):
    """Make sure text length does not exceed length by truncating if needed"""

    truncation_text = f"... (truncated from {len(text)} chars)"
    max_space = length - len(truncation_text)
    if max_space <= 30:
        raise ValueError(
            f"Cannot truncate string to {length}, "
            f"I need {len(truncation_text)} chars for the "
            f"truncation message itself. I would like to have at least"
            f"30 characters for the message."
        )
    if len(text) <= length:
        return text  # no truncation needed
    else:
        return text[:max_space] + truncation_text


class EntryPath:
    r"""Models an API path

    Like `\users`. The methods in this class would then represent entrypoints like
    `\users\find_all` or `\users\delete`.

    Notes
    -----
    Entrypoints fully parse server responses, raising exceptions for both http
    error responses and json parsing errors
    """

    @staticmethod
    def check_response(response):
        """Check response from PIMS server and raise appropriate exceptions

        Parameters
        ----------
        response: requests_mock.models.Response
            the http response to check

        Raises
        ------
        OperationForbidden(PIMSServerError)
            If an action is not allowed by PIMS for the logged-in user
        ResourceNotFound(PIMSServerError)
            If a 404 is returned
        OperationNotSupported(PIMSServerError)
            If a 405 is found
        """
        logger.debug(
            f"Checking response {response.status_code}: {truncate(response.text)}"
        )
        if response.status_code == 200:  # OK
            return response
        if response.status_code == 201:  # OK, created
            return response
        if response.status_code == 204:  # OK, deleted
            return response
        elif response.status_code == 400:
            raise BadRequest(response.text)
        elif response.status_code == 401:
            raise Unauthorized("401: Credentials do not seem to work")
        elif response.status_code == 403:
            raise OperationForbidden(response.text)
        elif response.status_code == 405:
            raise OperationNotSupported(response.text)
        elif response.status_code == 404:
            raise ResourceNotFound(response.text)
        else:
            msg = (
                f"Server returned status_code '{response.status_code}': "
                f"{response.text}"
            )
            raise PIMSServerError(truncate(msg))

    @staticmethod
    def parse_json_to_object(
        expected_obj_class: Type[pydantic.BaseModel], json_string: str
    ):
        """Try to parse json string as expected class

        Parameters
        ----------
        expected_obj_class
            The pydantic object class you expect to parse from json. Usually from the
            swagger_models module
        json_string
            The json returned by the server

        Returns
        -------
        instance of expected_obj_class

        Raises
        ------
        PIMSServerError
            If parsing does not work
        """
        try:
            return expected_obj_class.parse_obj(json.loads(json_string))
        except pydantic.ValidationError as e:
            raise PIMSServerError(
                f'Could not parse "{json_string[:30]}..." as'
                f" {expected_obj_class.__name__}"
            ) from e

    @classmethod
    def check_and_parse(
        cls,
        expected_obj_class: Type[pydantic.BaseModel],
        response: requests.Response,
    ):
        """Try to extract expected class instance from response

        Raises appropriate exceptions. Convenience method to use with most calls to
        API endpoints.

        Parameters
        ----------
        expected_obj_class
            The pydantic object class you expect to parse from json. Usually from the
            swagger_models module
        response
            Extract parsable info from this

        Raises
        ------
        PIMSServerError
            If anything goes wrong
        """
        logger.debug(f"Parsing {response.text}")
        cls.check_response(response)
        return cls.parse_json_to_object(expected_obj_class, response.text)


class Keyfiles(EntryPath):
    def __init__(self, base_url):
        self.url = f"{base_url}/Keyfiles"

    def get(self, session, key):
        """Get a specific key_file

        Parameters
        ----------
        session: requests.Session
            use this for getting
        key: int or str
            key for the key_file to get

        Raises
        ------
        PIMSServerError
            If anything goes wrong getting

        Returns
        -------
        KeyfileResponse
        """

        url = f"{self.url}/{str(key)}"
        return self.check_and_parse(KeyfileResponse, session.get(url))

    def get_all(self, session: requests.Session):
        """Get all keyfiles the currently logged-in user has access to

        Returns
        -------
        Iter[Keyfile]
        """

        raise NotImplementedError(
            "This is part of PIMS2 API V0 but has not been " "implemented yet"
        )


class Files(EntryPath):
    """Methods for KeyFiles/{KeyFileID}/Files/"""

    def __init__(self, base_url):
        self.base_url = base_url

    def get_entry_point(self, keyfile_id: Union[int, str]):
        """Entrypoint for files always contains keyfile_id

        Most of them do. Why?
        """
        return f"{self.base_url}/Keyfiles/{keyfile_id}/Files"

    def deidentify(self, session, keyfile_id, identifiers: List[Identifier]):
        """Find or create a pseudonym for each identifier

        PIMS return existing pseudonyms if found, otherwise generate based on the
        keyfile's pseudonym template

        Returns
        -------
        PseudonymisationResults
        """
        url = self.get_entry_point(keyfile_id) + "/deidentify"
        request = PseudonymisationRequest(
            fileOptions=FileOptions(
                suggestedHeaders=[
                    MyJsonDataHeader(
                        pseudonymisationAction=PseudonymisationAction.Identifier,
                        values=[x.value for x in identifiers],
                    ),
                    MyJsonDataHeader(
                        pseudonymisationAction=PseudonymisationAction.IdentitySource,
                        values=[x.source for x in identifiers],
                    ),
                ]
            ),
            targetKeyfileID=None,
            identitySource=None,
        )
        logger.debug(f"sending {request.json()}")

        return self.check_and_parse(
            PseudonymisationResults, session.post(url, json=request.dict())
        )


class Identities(EntryPath):
    def __init__(self, base_url):
        self.base_url = base_url

    def get_entry_point(self, keyfile_id: Union[int, str]):
        """Entrypoint for pseudonyms always contains keyfile_id"""
        return f"{self.base_url}/Keyfiles/{keyfile_id}/Identities"

    def get(
        self,
        session,
        keyfile_id: str,
        identity_value: str,
        identity_source: str,
    ):
        """Get an identity by value"""
        url = self.get_entry_point(keyfile_id)
        return self.check_and_parse(
            PseudonymIdentityResponse,
            session.get(
                url,
                params={
                    "identity": identity_value,
                    "identitySource": identity_source,
                },
            ),
        )

    def reidentify(self, session, keyfile_id, pseudonyms: List[Pseudonym]):
        """Find the identifier for each pseudonym

        Returns
        -------
        PseudonymisationResults
        """
        url = self.get_entry_point(keyfile_id) + "/reidentify"

        request = ReidentificationRequest(
            pseudonyms=PseudonymsReidentificationRequest(
                value=[x.value for x in pseudonyms]
            ),
            columns=None,
            targetKeyfileID=None,
            activityID=None,
        )

        logger.debug(f"sending {request.json()} to {url}")

        return self.check_and_parse(
            ReidentificationResult,
            response=session.post(
                url, params={"returnIdentities": True}, json=request.dict()
            ),
        )

    def exists(self, session, keyfile_id, identities: List[Identifier]):
        url = self.get_entry_point(keyfile_id) + "/exists"

        existence_data: Dict[Identifier, bool] = {}
        # we have to collect info per source
        per_source = defaultdict(list)
        for x in identities:
            per_source[x.source].append(x)
        for source, ids in per_source.items():
            request = IdentitiesRequest(
                identitySource=source, identities=[x.value for x in ids]
            )
            response = session.post(url, json=request.dict())

            for requested, (returned, exists) in zip(
                ids, response.json().items()
            ):
                if (
                    requested.value != returned
                ):  # I don't trust this response order
                    raise ValueError(
                        f'Requested "{requested}" but got ' f"back {returned}"
                    )
                existence_data[requested] = exists

        return existence_data


class Pseudonyms(EntryPath):
    def __init__(self, base_url):
        self.base_url = base_url

    def get_entry_point(self, keyfile_id: Union[int, str]):
        """Entrypoint for pseudonyms always contains keyfile_id"""
        return f"{self.base_url}/Keyfiles/{keyfile_id}/Pseudonyms"

    def exists(self, session, keyfile_id, pseudonyms: List[Pseudonym]):
        url = self.get_entry_point(keyfile_id) + "/exists"

        existence_data: Dict[Pseudonym, bool] = {}
        request = PseudonymsRequest(pseudonyms=[x.value for x in pseudonyms])
        response = session.post(url, json=request.dict())

        for requested, (returned, exists) in zip(
            pseudonyms, response.json().items()
        ):
            if (
                requested.value != returned
            ):  # I Don't trust this response order
                raise ValueError(
                    f'Requested "{requested}" but got ' f"back {returned}"
                )
            existence_data[requested] = exists

        return existence_data


class PIMSServerError(PIMSError):
    pass


class BadRequest(PIMSServerError):
    pass


class Unauthorized(PIMSServerError):
    pass


class OperationForbidden(PIMSServerError):
    pass


class OperationNotSupported(PIMSServerError):
    pass


class ResourceNotFound(PIMSServerError):
    pass


class OverWriteAction:
    """What to do if data already exists in PIMS?"""

    ADD = 1  # Add data in duplicate column
    OVERWRITE = 2
    SKIP = 3
