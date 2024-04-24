"""Models interactions with a PIMS Server

Client is used by core, and translates and handles all communication with the actual
PIMS server.
"""
from typing import List, Union

from pimsclient.keyfile import KeyFile, PimsElement
from pimsclient.server import PIMSServer
from pimsclient.core import (
    Identifier,
    Key,
    Pseudonym,
)
from pimsclient.exceptions import PIMSClientError
from pimsclient.autogen.swagger_models_v0 import (
    PseudonymIdentityResponse,
    PseudonymisationAction,
)


class AuthenticatedClient:
    def __init__(self, session):
        """A client with a valid session. Translates between server responses and
        core objects.

        Parameters
        ----------
        session: requests.Session
            Use this for communicating with PIMS

        """
        self.session = session

    def get_key_file_response(self, key: Union[str, int], server: PIMSServer):
        """Create a KeyFile based on server response and this client

        Parameters
        ----------
        key
            The id of the keyfile to get
        server
            The server to query

        Raises
        ------
        PIMSServerError
            When key file cannot be got for some reason

        Returns
        -------
        KeyfileResponse
        """
        return server.keyfiles.get(session=self.session, key=key)

    def pseudonymize(
        self,
        server: PIMSServer,
        keyfile_id: str,
        identifiers: List[Identifier],
    ):
        """Get a pseudonym for each identifier. If identifier is known in PIMS,
        return this. Otherwise, have PIMS generate a new pseudonym and return that.

        Parameters
        ----------
        server:
            Server to call
        keyfile_id:
            Keyfile to use
        identifiers: List[Identifier]
            The identifiers to get pseudonyms for

        Returns
        -------
        List[Key]
            The PIMS pseudonym for each identifier
        """

        response = server.files.deidentify(
            session=self.session,
            keyfile_id=keyfile_id,
            identifiers=identifiers,
        )
        response_elements = {
            x.pseudonymisationAction: x for x in response.results
        }

        try:
            pseudonyms = response_elements[
                PseudonymisationAction.PseudonymOutput
            ].values
        except KeyError as e:
            raise PIMSClientError(
                "Expected Pseudonyms to be returned but could not "
                f"find any. Sent in {identifiers}"
            ) from e
        if len(identifiers) != len(pseudonyms):  # just being careful
            raise PIMSClientError(
                f"Sent in {len(identifiers)} identifies, but got "
                f"back {len(pseudonyms)} pseudonyms. Not good."
            )

        return [
            Key.init_from_strings(
                pseudonym=pseudonym,
                identity=identity.value,
                identity_source=identity.source,
            )
            for pseudonym, identity in zip(pseudonyms, identifiers)
        ]

    def delete(self, server, keyfile_id: str, identifiers: List[Identifier]):
        """Get a pseudonym for each identifier. If identifier is known in PIMS,
        return this. Otherwise, have PIMS generate a new pseudonym and return that.

        Parameters
        ----------
        server:
            Server to call
        keyfile_id:
            Keyfile to use
        identifiers: List[Identifier]
            The identifiers to get pseudonyms for

        Returns
        -------
        List[Key]
            The PIMS pseudonym for each identifier
        """
        raise NotImplementedError(
            "This is part of PIMS2 API V0 but has not been " "implemented yet"
        )

    def set(self, server, keyfile_id: str, identifiers: List[Identifier]):
        """Get a pseudonym for each identifier. If identifier is known in PIMS,
        return this. Otherwise, have PIMS generate a new pseudonym and return that.

        Parameters
        ----------
        server:
            Server to call
        keyfile_id:
            Keyfile to use
        identifiers: List[Identifier]
            The identifiers to get pseudonyms for

        Returns
        -------
        List[Key]
            The PIMS pseudonym for each identifier
        """
        raise NotImplementedError(
            "This is part of PIMS2 API V0 but has not been " "implemented yet"
        )

    def reidentify(
        self, server: PIMSServer, keyfile_id: str, pseudonyms: List[Pseudonym]
    ) -> List[Key]:
        """Find the identifiers linked to the given pseudonyms.

        Parameters
        ----------
        server:
            Server to call
        keyfile_id:
            Keyfile to use
        pseudonyms: List[Pseudonym]
            The pseudonyms to get identifiers for

        Returns
        -------
        List[Key]
            A list of pseudonym-identifier keys

        Raises
        ------
        IdentityNotFoundError
            If any given pseudonym could not be reidentified

        """

        result = server.identities.reidentify(
            session=self.session, keyfile_id=keyfile_id, pseudonyms=pseudonyms
        )

        # Two identities from different sources can have the same pseudonym
        # If such a pseudonym is requested, PIMS returns all matching identities
        # Rematch here
        requested = [(x.value, x.source) for x in pseudonyms]
        received = {
            (x.pseudonym, x.identitySource): x for x in result.pseudonyms.items
        }

        remapped: List[PseudonymIdentityResponse] = []
        for key in requested:
            try:
                remapped.append(received[key])
            except KeyError as e:
                raise IdentityNotFoundError(
                    f"Requested reidentification of {key}. But this was not in "
                    f"returned response"
                ) from e

        return [
            Key.init_from_strings(
                pseudonym=x.pseudonym,  # type: ignore
                identity=x.value,  # type: ignore
                identity_source=x.identitySource,  # type: ignore
            )
            for x in remapped
        ]

    def exists(
        self, server: PIMSServer, keyfile_id: str, elements: List[PimsElement]
    ):
        # separate objects for separate calls
        identities = []
        pseudonyms = []
        for x in elements:
            if isinstance(x, Identifier):
                identities.append(x)
            elif isinstance(x, Pseudonym):
                pseudonyms.append(x)
            else:
                raise ValueError(
                    f"Expected Identifier or Pseudonym, found {type(x)}"
                )

        result = server.identities.exists(
            session=self.session, keyfile_id=keyfile_id, identities=identities
        )

        result.update(
            server.pseudonyms.exists(
                session=self.session,
                keyfile_id=keyfile_id,
                pseudonyms=pseudonyms,
            )
        )

        return result

    def set_keys(self, key_file: KeyFile, keys: List[Key]):
        """Manually set the given pseudonym-identifier keys

        Raises
        ------
        PIMSServerError
            If any pseudonym or identifier already exists in keyfile

        """
        raise NotImplementedError(
            "This is part of PIMS2 API V0 but has not been " "implemented yet"
        )


class PseudonymTemplate:
    """The way new pseudonyms are generated in PIMS for a single pseudonym type"""

    def __init__(self, template_string, pseudonym_class):
        """Create a new pseudonym template

        Parameters
        ----------
        template_string: str
            string representing template. See PIMS documentation for options
        pseudonym_class: class
            The TypedPseudonym class for which this template holds

        Notes
        -----
        In this client library a 'PseudonymTemplate' is the template used for
        generating values for a single datatype In a PIMS KeyFile,
        'pseudonym template' refers to a long string representing templates for
        ALL datatypes, separated by a separator. The PIMS naming is outdated as
        it was not designed with multiple datatypes in mind therefore the client
        library will not follow this naming

        """
        self.template_string = template_string
        self.pseudonym_class = pseudonym_class

    def as_pims_string(self):
        return f":{self.pseudonym_class.value_type}|{self.template_string}"


class PIMSProjectException(PIMSClientError):
    pass


class IdentityNotFoundError(PIMSClientError):
    pass
