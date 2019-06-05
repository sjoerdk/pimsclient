"""
Objects and classes that can be directly mapped to the PIMS Swagger API. Retrieving, Saving, Error handling

"""
from pimsclient.client import Key
from collections import defaultdict


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
        raise NotImplemented()

    def to_dict(self):
        """

        Returns
        -------
        dict
            A dictionary representation of this object

        """
        raise NotImplemented()


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


class SwaggerEntryPoint:
    """A part of a swagger API that can be directly mapped to a URL path, like /Pseudonyms or /Users

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
        super(KeyFiles, self).__init__(session)

    def get(self, key):
        """Get a specific key_file

        Parameters
        ----------
        key: int or str
            key for the key_file to get

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
        List(KeyFile)
        """
        url = f"{self.url}/ForUser/{str(user.key)}"
        fields = self.session.get(url)
        return [KeyFile.from_dict(x) for x in fields["Data"]]

    def pseudonymize(self, key_file, identifiers):
        """get a pseudonym for each identifier. If identifier is known in PIMS, return this. Otherwise,
        have PIMS generate a new pseudonym and return that.

        Parameters
        ----------
        identifiers: List[Identifier]
            The identifiers to get pseudonyms for
        key_file: KeyFile
            The key_file to use

        Returns
        -------
        List[Key]
            The PIMS pseudonym for each identifier

        """
        url = f"{self.url}/{key_file.key}/Files/Deidentify"

        keys = []
        per_source = defaultdict(list)
        for x in identifiers:
            per_source[x.source].append(x)
        for source, items in per_source.items():
            data = [{"Name": "Column 1", "Type": ["Pseudonymize"], "Action": "Pseudonymize",
                        "values":[x.value for x in items]}]

            params = {'FileName': 'DataEntry',
                      'identity_source': source,
                      'CreateOutputfile': True,
                      'overwrite': 'Overwrite'}

            raise NotImplemented("Waiting for fix in PIMS functionality")
            fields = self.session.post(url, params=params, json_payload=data)
            keys.append(
                Key.init_from_strings(
                    pseudonym=fields["Pseudonym"],
                    identity=fields["Identifier"],
                    identity_source=fields["IdentitySource"],
                )
            )
        return keys

    def pseudonymize_legacy(self, key_file, identifiers):
        """get a pseudonym for each identifier. If identifier is known in PIMS, return this. Otherwise,
        have PIMS generate a new pseudonym and return that.
        Parameters
        ----------
        identifiers: List[Identifier]
            The identifiers to get pseudonyms for
        key_file: KeyFile
            The key_file to use
        Returns
        -------
        List[Key]
            The PIMS pseudonym for each identifier
        """

        url = f"{self.url}/{key_file.key}/Pseudonyms"
        keys = []
        for identifier in identifiers:
            fields = self.session.post(url, params=identifier.to_dict())
            keys.append(Key.init_from_strings(pseudonym=fields['Pseudonym'],
                                              identity=fields['Identifier'],
                                              identity_source=fields['IdentitySource']))

        return keys

    def reidentify(self, key_file, pseudonyms):
        """Find the identifiers linked to the given pseudonyms.

        Parameters
        ----------
        key_file: KeyFile
            The key_file to use
        pseudonyms: List[Pseudonym]
            The pseudonyms to get identifyers for

        Notes
        -----
        Returned list might be shorter than input list. For unknown pseudonyms no keys are returned

        Returns
        -------
        List[Key]
            A list of pseudonym-identifier keys

        """
        url = f"{self.url}/{key_file.key}/Pseudonyms/Reidentify"
        fields = self.session.post(
            url,
            params={
                "ReturnIdentity": True,
                "ReturnColumns": "*",
                "items": [x.value for x in pseudonyms],
            },
        )
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


class Users(SwaggerEntryPoint):

    url_path = "/Users"

    def __init__(self, session):
        super(Users, self).__init__(session)

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
