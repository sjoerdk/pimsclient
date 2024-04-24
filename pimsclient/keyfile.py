"""The main object user-facing object in pimsclient. An authenticated connection to a
specific keyfile in a specific server. After initialization you should be able to use
the KeyFile object for all your pseudonymization

Examples
--------
```
    keyfile = KeyFile(id=123, AuthenticatedClient(session=session))
    keyfile.name
    >>> "My keyfile"
    key = keyfile.pseudonymize(PatientID("realpatient"))
    key.identifier.value
    >>>  "realpatient"
    key.pseudonym.value
    >>>  "patient123"
```

Keyfile is in its own module separate from core to avoid circular imports. Circular
imports are due to KeyFile combining client server and core code
"""
from typing import Dict, List, Union

from pimsclient.exceptions import InvalidPseudonymTemplateError
from pimsclient.core import Identifier, Key, Pseudonym


PimsElement = Union[Pseudonym, Identifier]


class KeyFile:
    """An authenticated connection to a PIMS key file in a specific server. Main
    interface for working with PIMS.
    """

    def __init__(
        self,
        info,
        client,
        server,
    ):
        """

        Parameters
        ----------
        info: KeyfileResponse
            What is known about this keyfile on the server. Name, description etc.
        client: AuthenticatedClient
            Use this client to query
        server: PIMSServer
            Send queries to this server
        """
        self.info = info
        self.client = client
        self.server = server

    def __str__(self):
        return f"KeyFile #{self.id}: '{self.name}' - ('{self.description}')"

    @classmethod
    def init_from_id(
        cls,
        keyfile_id,
        client,
        server,
    ):
        """Initialize a keyfile by querying server for keyfile id.

        Saves you having to call key file response
        Parameters
        ----------
        keyfile_id: int

        client: AuthenticatedClient

        server: PIMSServer

        Returns
        -------
        KeyFile

        """
        return cls(
            info=client.get_key_file_response(key=keyfile_id, server=server),
            client=client,
            server=server,
        )

    @property
    def name(self):
        return self.info.name

    @property
    def pseudonym_template(self):
        return self.info.pseudonymTemplate

    @property
    def members(self):
        return self.info.members

    @property
    def description(self):
        return self.info.description

    @property
    def id(self):
        return self.info.id

    def pseudonymize(self, identifiers: List[Identifier]):
        """Get a pseudonym from PIMS for each identifier in list

        Parameters
        ----------
        identifiers: List[TypedIdentifier]
            identifiers to pseudonymize

        Raises
        ------
        PIMSClientError
            If pseudonymization fails

        Returns
        -------
        List[TypedKey]
            Each identifier mapped to PIMS pseudonym

        """
        return self.client.pseudonymize(
            server=self.server,
            keyfile_id=str(self.id),
            identifiers=identifiers,
        )

    def delete(self, identifiers: List[Identifier]):
        """Delete the given identifiers from server

        Parameters
        ----------
        identifiers: List[TypedIdentifier]
            identifiers to pseudonymize

        Raises
        ------
        PIMSClientError
            If deleting fails

        """
        self.client.delete(
            server=self.server,
            keyfile_id=str(self.id),
            identifiers=identifiers,
        )

    def reidentify(self, pseudonyms: List[Pseudonym]) -> List[Key]:
        """Get identifiers for each pseudonym in list

        Parameters
        ----------
        pseudonyms:
            list of pseudonyms to process

        Raises
        ------
        PIMSClientException
            If any pseudonym could not be reidentified

        Returns
        -------
        List[TypedKey]
            Pseudonym mapped to identifier if found. If a pseudonym is not
            found in PIMS it is omitted from list

        """
        return self.client.reidentify(
            server=self.server, keyfile_id=str(self.id), pseudonyms=pseudonyms
        )

    def exists(self, elements: List[PimsElement]) -> Dict[PimsElement, bool]:
        """Check whether the given pseudonyms and identifiers exist"""

        return self.client.exists(
            server=self.server, keyfile_id=str(self.id), elements=elements
        )

    def assert_pseudonym_templates(self, should_have_a_template, should_exist):
        """Make sure the pseudonym templates for the datatypes in this project
         are as expected.

        This check makes sure the format UID's makes sense. For example, if no
        template is defined for StudyInstanceUID, de-identifying might yield a guid,
        which is not a valid DICOM UID. Fail early in this case, because this will
        cause headaches later if not fixed.

        Notes
        -----
        In this client library a 'PseudonymTemplate' is for a single datatype.
        In PIMS, the pseudonym template contains templates for all datatypes.
        See notes for PseudonymTemplate


        Parameters
        ----------
        should_have_a_template: List[pimsclient.core.TypedPseudonym]
            These pseudonym types should have a template defined in this project,
            regardless of what the actual template
            is.
        should_exist: List[PseudonymTemplate]
            These exact templates should be defined in this project. Requires the
            template to be exactly a certain value

        Raises
        ------
        PIMSClientError
            When assertion cannot be done. For example when connection to server
            fails
        InvalidPseudonymTemplateError:
            When this project's template is not as expected

        """

        pims_template = self.pseudonym_template
        for typed_pseudonym in should_have_a_template:
            if f":{typed_pseudonym.value_type}" not in pims_template:
                msg = (
                    f'Could not find any template for "{typed_pseudonym}" in '
                    f'project {self} template "{pims_template}".'
                    f" This is required"
                )
                raise InvalidPseudonymTemplateError(msg)

        for template in should_exist:
            if template.as_pims_string() not in pims_template:
                msg = (
                    f'Could not find "{template.as_pims_string()}" in project'
                    f' {self} template "{pims_template}".'
                    f" This is required"
                )
                raise InvalidPseudonymTemplateError(msg)
