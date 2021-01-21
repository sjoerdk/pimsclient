"""Objects and classes that can be directly mapped to the PIMS Swagger API.
Retrieving, Saving, Error handling

"""
from collections import defaultdict
from typing import List


class SwaggerObject:
    """A python object that can have a mirror object accessed via a swagger web API

    This object can be retrieved from, saved to a Swagger web API
    """

    @classmethod
    def from_dict(cls, dict_in):
        """
        Parameters
        ----------
        dict_in: Dict
            A dictionary representing this object

        Returns
        -------
        SwaggerObject
            an instance of this object

        """
        raise NotImplementedError()

    def to_dict(self):
        """

        Returns
        -------
        dict
            A dictionary representation of this object

        """
        raise NotImplementedError()


class KeyFile(SwaggerObject):
    def __init__(self, key, name, description="", pseudonym_template="Guid"):
        """A table of pseudonyms

        Parameters
        ----------
        key: str
            swagger key for this key_file
        name: str
            short name for this key_file. No spaces allowed
        description: str
            Description of this key_file
        pseudonym_template: str
            Template for creating new pseudonyms. See PIMS documentation for format
        """
        self.key = key
        self.name = name
        self.description = description
        self.pseudonym_template = pseudonym_template

    def __str__(self):
        return f'KeyFile "{self.name}" (key={self.key})'

    def to_dict(self):
        return {
            "KeyfileKey": self.key,
            "Name": self.name,
            "Description": self.description,
            "PseudonymTemplate": self.pseudonym_template,
        }

    @classmethod
    def from_dict(cls, dict_in):
        return cls(
            key=dict_in["KeyfileKey"],
            name=dict_in["Name"],
            description=dict_in["Description"],
            pseudonym_template=dict_in["PseudonymTemplate"],
        )


class User(SwaggerObject):
    def __init__(self, key, name, email, role):
        """A PIMS user

        Parameters
        ----------
        key: str
            swagger key for this user
        name: str
            name of the user, no spaces allowed
        email: str
            user email
        role: str
            Base role for user, as assigned in Swagger
        """
        self.key = key
        self.name = name
        self.email = email
        self.role = role

    def __str__(self):
        return f'User "{self.name}" <{self.email}> (key={self.key})'

    def to_dict(self):
        return {
            "UserKey": self.key,
            "Name": self.name,
            "Email": self.email,
            "BaseRole": self.role,
        }

    @classmethod
    def from_dict(cls, dict_in):
        return cls(
            key=dict_in["UserKey"],
            name=dict_in["Name"],
            email=dict_in["Email"],
            role=dict_in["BaseRole"],
        )


class OverWriteAction:
    """What to do if data already exists in PIMS?"""

    ADD = 1  # Add data in duplicate column
    OVERWRITE = 2
    SKIP = 3


class SwaggerEntryPoint:
    """A part of a swagger API that can be directly mapped to a URL path, like
     /Pseudonyms or /Users

    Includes logged-in session

    """

    url_path = None

    def __init__(self, session):
        """

        Parameters
        ----------
        session: PIMSSession
            session to use when communicating with this entry point
        """
        self.session = session
        self.url = f"{session.base_url}{self.url_path}"

    def __str__(self):
        return f"Swagger entrypoint '{self.url_path}' trough session {self.session}"


class KeyFiles(SwaggerEntryPoint):

    url_path = "/Keyfiles"

    def __init__(self, session):
        super().__init__(session)

    def get(self, key):
        """Get a specific key_file

        Parameters
        ----------
        key: int or str
            key for the key_file to get

        Raises
        ------
        PIMSServerException
            If anything goes wrong getting

        Returns
        -------
        KeyFile
        """

        url = f"{self.url}/{str(key)}"
        fields = self.session.get(url)
        return KeyFile.from_dict(fields)

    def get_all(self, user):
        """Get all keyfiles for given user

        Parameters
        ----------
        user: User
            user to get keyfiles for

        Returns
        -------
        List[KeyFile]
        """
        url = f"{self.url}/ForUser/{str(user.key)}"
        fields = self.session.get(url)
        return [KeyFile.from_dict(x) for x in fields["Data"]]

    def pseudonymize(
        self, key_file: KeyFile, identifiers: List["Identifier"]
    ) -> List["Key"]:
        """Get a pseudonym for each identifier. If identifier is known in PIMS,
        return this. Otherwise, have PIMS generate a new pseudonym and return that.

        Parameters
        ----------
        identifiers: List[Identifier]
            The identifiers to get pseudonyms for
        key_file: KeyFile
            The key_file to use

        Notes
        -----
        Each call this function calls PIMS API twice for each unique source in
        identifiers. This is result of the way the API can be called

        Returns
        -------
        List[Key]
            The PIMS pseudonym for each identifier

        """
        keys = []
        # Each call to process a list of identifiers only allows a single source.
        # Split identifiers by source
        per_source = defaultdict(list)
        for x in identifiers:
            per_source[x.source].append(x)
        for source, items in per_source.items():
            keys = keys + self.deidentify(key_file, [x.value for x in items], source)

        return keys

    def deidentify(
        self, key_file: KeyFile, values: List[str], source: str
    ) -> List["Key"]:
        """Direct mapping to /Deidentify. Send items to PIMS to be assigned a
        pseudonym Will split values over multiple API calls when there are too many
        to fit in single API request.

        Parameters
        ----------
        key_file: KeyFile
            The key_file to use
        values: List[str]
            Values to deidentify
        source: str
            source to register in PIMS for each value. Typically one of
            client.ValueTypes

        Returns
        -------
        List[Key]
            The PIMS pseudonym for each identifier

        """

        url = f"{self.url}/{key_file.key}/Files/Deidentify"
        page_size = 1000  # happens to be the limit for this server
        keys = []

        while values:
            values_chunk = values[:page_size]
            values = values[page_size:]

            data = [
                {
                    "Name": "Column 1",
                    "Type": ["Pseudonymize"],
                    "Action": "Pseudonymize",
                    "values": [x for x in values_chunk] + [""],
                }
            ]  # add empty item because of bug in PIMS (#8671)
            params = {
                "FileName": "DataEntry",
                "identity_source": source,
                "CreateJsonOutput": True,
                "overwrite": "Overwrite",
                "PageSize": page_size,
            }

            pseudonyms = self.parse_deidentify_response(
                self.session.post(url, params=params, json_payload=data)
            )

            keys = keys + [
                Key.init_from_strings(pseudonym=x, identity=y, identity_source=source)
                for x, y in zip(pseudonyms, values_chunk)
            ]

        return keys

    def set_keys(self, key_file: KeyFile, keys: List["Key"]):
        """Set pseudonym/identifier pairs in PIMS. This overrules automatic pseudonym
        generation by pims. Pages calls and makes separate call for each type of Key
        in keys

        Raises
        ------
        PIMSServerException
            When trying to set a pseudonym that already exists in keyfile
        """

        url = f"{self.url}/{key_file.key}/Files/Deidentify"
        page_size = 1000  # happens to be the limit for this server

        per_source = defaultdict(list)
        for x in keys:
            per_source[x.source()].append(x)
        for source, items in per_source.items():

            while items:
                keys_chunk = items[:page_size]
                items = keys[page_size:]

                data = [
                    {
                        "Name": "Column 1",
                        "Action": "UseAsPseudonym",
                        "Values": [x.pseudonym.value for x in keys_chunk] + [""],
                    },
                    {
                        "Name": "Column 2",
                        "Action": "Pseudonymize",
                        "Values": [x.identifier.value for x in keys_chunk] + [""],
                    },
                ]  # add empty items because of bug in PIMS (#8671)
                params = {
                    "FileName": "DataEntry",
                    "identity_source": source,
                    "CreateJsonOutput": True,
                    "overwrite": OverWriteAction.OVERWRITE,
                    "PageSize": page_size,
                }

                self.session.post(url, params=params, json_payload=data)

    def reidentify(self, key_file, pseudonyms, chunk_size=500):
        """Find the identifiers linked to the given pseudonyms.

        Parameters
        ----------
        key_file: KeyFile
            The key_file to use
        pseudonyms: List[Pseudonym]
            The pseudonyms to get identifiers for
        chunk_size: int, optional
            Maximum number of identifiers to process per API call. Defaults to 500

        Notes
        -----
        * Returned list might be shorter than input list. For unknown pseudonyms no
          keys are returned
        * Every unique source in pseudonyms list yields one https call to API

        Returns
        -------
        List[Key]
            A list of pseudonym-identifier keys

        """
        url = f"{self.url}/{key_file.key}/Pseudonyms/Reidentify"

        keys = []
        per_source = defaultdict(list)
        for x in pseudonyms:
            per_source[x.source].append(x)
        for source, items in per_source.items():
            while items:
                items_chunk = items[:chunk_size]
                items = items[chunk_size:]
                fields = self.session.post(
                    url,
                    params={
                        "ReturnIdentity": True,
                        "ReturnColumns": "*",
                        "items": [x.value for x in items_chunk],
                        "PageSize": chunk_size,
                    },
                )
                #  If multiple data types have the same pseudonym value, PIMS will
                #  return all. E.g. is there is a patient and a study that are both
                #  called '1234', PIMS will return 2 results for one query to '1234'.
                #  Filter only the results that were asked for. This cannot be
                #  filtered properly in the POST request.
                keys = keys + [
                    x for x in self.fields_to_keys(fields) if x.source() == source
                ]

        return keys

    def get_pseudonyms_by_action(self, key_file, action_id):
        """Find the pseudonyms linked to the given action_id

        Parameters
        ----------
        key_file: KeyFile
            The key_file to use
        action_id: int
            action id to get

        Returns
        -------
        List[Key]
            A list of pseudonym-identifier keys

        """
        url = f"{self.url}/{key_file.key}/Pseudonyms/Action/{action_id}"

        return self.session.get(url)

    @staticmethod
    def fields_to_keys(fields):
        """Parses standard multi-key API response to a list of Keys

        Parameters
        ----------
        fields: Dict
            The standard type of response given by the Swagger API when multiple identity-pseuonym pairs are returned.
            For a good example see tests.factories.RequestsMockResponseExamples.KEYFILES_PSEUDONYMS_REIDENTIFY_RESPONSE

        Returns
        -------
        List[Key]

        """
        data = {
            x["Name"]: x["Values"] for x in fields["Data"]
        }  # data is returned in separate lists
        keys = [
            Key.init_from_strings(x, y, z)
            for x, y, z in zip(
                data["Pseudonyms"], data["Identity"], data["Identity Source"]
            )
        ]
        return keys

    def get_users(self, key_file):
        url = f"{self.url}/{key_file.key}/Users"
        fields = self.session.get(url)
        return [User.from_dict(x) for x in fields["Data"]]

    @staticmethod
    def parse_deidentify_response(response):
        """Parse the response of /Keyfiles/{KeyfileKey}/Files/Deidentify when
        CreatJsonOutput=True has been passed.

        This function was added later to the API and I don't trust it fully.
        Do some extra sanity checks

        Parameters
        ----------
        response: Dict
            Response from sever, already parsed to dictionary

        Raises
        ------
        DeidentifyResponseParsingException
            When the response contains more than one pseudonym for any identity.
            This could potentially happen when two identifiers have different
            identifier_source values. This code has not been designed for this.

        Returns
        -------
        List[str]
            list of pseudonyms that were created

        """

        try:
            return [pseudonym for _, pseudonym in response["Data"]]
        except ValueError as e:
            msg = f"Expected an empty line and a pseudonym. Error: '{e}'.."
            raise DeidentifyResponseParsingException(msg)


class Users(SwaggerEntryPoint):

    url_path = "/Users"

    def __init__(self, session):
        super().__init__(session)

    def get(self, key):
        """Get a specific user

        Parameters
        ----------
        key: int or str
            key for the user to get

        Returns
        -------
        User
        """

        url = f"{self.url}/{str(key)}/Details"
        fields = self.session.get(url)["Data"][
            0
        ]  # server returns a paginated response with one entry
        return User.from_dict(fields)


class Identifier:
    def __init__(self, value, source):
        """A real patientID, StudyInstance or the like, with a source

        Parameters
        ----------
        value: str
            PatientID, StudyInstance or whatever should be pseudonymized
        source: str
            Source for this value, like the hospital where the PatientID is used. Used for disambiguation
        """
        self.value = value
        self.source = source

    def __str__(self):
        return f"Identifier '{self.value}' (source:'{self.source}')"

    def to_dict(self):
        return {"identifier": self.value, "identity_source": self.source}


class Pseudonym:
    def __init__(self, value, source=None):
        """A pseudonym for an actual identifier.

        Parameters
        ----------
        value: str
            The value of this pseudonym, like 'Patient1' or 'Case_23'
        source: str, optional
            Source for this value. Defaults to None
        """
        self.value = value
        self.source = source

    def __str__(self):
        return f"Pseudonym '{self.value}' (source:'{self.source}')"

    def __eq__(self, other):
        return self.value == other.value and self.source == other.source


class Key:
    def __init__(self, identifier, pseudonym):
        """Links an identifier with a pseudonym

        Parameters
        ----------
        identifier: Identifier
            Real identifier, like 'Yen Hu'
        pseudonym:
            Pseudonym used for the identifyer, like 'Case3'
        """
        self.identifier = identifier
        self.pseudonym = pseudonym

    @classmethod
    def init_from_strings(
        cls, pseudonym: str, identity: str, identity_source: str
    ) -> "Key":
        """Creates a Key from string-only input arguments. For convenience"""
        return cls(
            identifier=Identifier(value=identity, source=identity_source),
            pseudonym=Pseudonym(value=pseudonym, source=identity_source),
        )

    def source(self):
        """Returns the source for this key. Source should be the same in both
        identifier and pseudonym
        """
        return self.identifier.source

    def __str__(self):
        return f"Key {self.pseudonym.value}"

    def describe(self) -> str:
        """Describe this Key like like 'orginal -> pseudonym'"""
        return f"{self.identifier.value} -> {self.pseudonym.value}"


class PIMSSwaggerException(Exception):
    pass


class DeidentifyResponseParsingException(PIMSSwaggerException):
    pass
