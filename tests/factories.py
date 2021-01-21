from typing import Tuple
from unittest.mock import Mock

import factory
from factory import fuzzy

from requests.models import Response

from pimsclient.client import (
    ValueTypes,
    TypedKey,
    TypedPseudonym,
    PatientID,
    PseudoPatientID,
)
from pimsclient.swagger import User, KeyFile, Identifier, Pseudonym, Key


class UserFactory(factory.Factory):
    class Meta:
        model = User

    key = factory.Sequence(lambda n: f"{n}")
    name = factory.Faker("first_name")
    email = factory.LazyAttribute(lambda a: f"{a.name}@radboudumc.nl".lower())
    role = "TEST_ROLE"


class KeyFileFactory(factory.Factory):
    class Meta:
        model = KeyFile

    key = factory.Sequence(lambda n: f"{n}")
    name = factory.Faker("first_name")
    description = factory.Faker("sentence", nb_words=8)
    pseudonym_template = factory.Faker(
        "sentence", ext_word_list=["S8|", "text|", "ID#|"]
    )


class PseudonymFactory(factory.Factory):
    class Meta:
        model = Pseudonym

    value = factory.Sequence(lambda n: f"pseudonym{n}")


class IdentifierFactory(factory.Factory):
    class Meta:
        model = Identifier

    value = factory.Faker("first_name")
    source = "generated_by_factory"


class TypedIdentifierFactory(factory.Factory):
    """An identifier that can be interpreted as having a valid value type"""

    class Meta:
        model = Identifier

    value = factory.Faker("first_name")
    source = fuzzy.FuzzyChoice(ValueTypes.all)


class PatientIDFactory(factory.Factory):
    """An identifier that can be interpreted as being a PatientID"""

    class Meta:
        model = PatientID

    value = factory.Faker("first_name")


class TypedPseudonymFactory(factory.Factory):
    """A Pseudonym that can be interpreted as having a valid value type"""

    class Meta:
        model = TypedPseudonym

    value = factory.Faker("first_name")
    source = fuzzy.FuzzyChoice(ValueTypes.all)


class PseudoPatientIDFactory(factory.Factory):
    """A Pseudonym for a PatientID"""

    class Meta:
        model = PseudoPatientID

    value = factory.Faker("first_name")


class KeyFactory(factory.Factory):
    class Meta:
        model = Key

    identifier = factory.SubFactory(IdentifierFactory)
    pseudonym = factory.SubFactory(PseudonymFactory)


class TypedKeyFactory(factory.Factory):
    class Meta:
        model = TypedKey

    identifier = factory.SubFactory(TypedIdentifierFactory)
    pseudonym = factory.SubFactory(PseudonymFactory)


class RequestsMock:
    """Can be put in place of the requests module. Does not hit any server but
    returns kind of realistic arbitrary responses
    """

    def __init__(self):
        self.requests_mock = Mock()  # for keeping track of past requests_mock

    def set_response_tuple(self, tuple: Tuple[int, str]):
        """Any call to get() or post() will yield a Response() object with the
        given parameters
        """
        self.set_response(text=tuple[1], status_code=tuple[0])

    def set_response(self, text, status_code=200):
        """Any call to get() or post() will yield a Response() object with the
        given parameters

        Parameters
        ----------
        text: str
            content to return
        status_code: int, optional
            http return code. Defaults to 200

        """
        response = Response()
        response.encoding = "utf-8"
        response.status_code = status_code
        response._content = bytes(text, response.encoding)

        self.requests_mock.get.return_value = response
        self.requests_mock.post.return_value = response

    def set_response_exception(self, exception):
        """Any call to get() or post() will yield the given exception"""

        self.requests_mock.get.side_effect = exception
        self.requests_mock.post.side_effect = exception

    def get(self, *args, **kwargs):
        return self.requests_mock.get(*args, **kwargs)

    def post(self, *args, **kwargs):
        return self.requests_mock.post(*args, **kwargs)

    def reset(self):
        self.requests_mock.reset_mock()

    def called(self):
        """True if either get() or post() was called"""
        return self.requests_mock.get.called or self.requests_mock.post.called

    @staticmethod
    def Session():  # noqa: N802 capitalized to match Requests module function
        return Mock()


class RequestsMockResponseExamples:
    """Some examples of http response texts that a PIMS Swagger API can return"""

    INVALID_API_REQUEST = (400, r': "Bad request!"')

    KEYFILE_DOES_NOT_EXIST = (404, r': "Keyfile does not exist (anymore)"')

    UNAUTHORIZED = (401, r"Unauthorized, your credentials do not work here")

    ACTION_REFUSED_INSUFFICIENT_RIGHTS = (
        403,
        r"Action refused due to insufficient rights: Test message",
    )

    REQUESTED_RESOURCE_DOES_NOT_SUPPORT = (
        405,
        r'{Message":"The requested resource does not support http method \'GET\'}',
    )

    UNKNOWN_ERROR = (781, r': "Excessively Exotic Error"')

    UKNOWN_URL = (
        404,
        r'"<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" '
        r'"http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd"> \
              <h2>404 - File or directory not found.</h2>"',
    )

    KEYFILES_FORUSER_RESPONSE = (
        200,
        '{ "Count": 0, "Page": 0, "PageSize": 0, "PageCount": 0, "Data": [ '
        '{ "CreationDate": "2019-05-29T11:32:09.723Z", "SequenceNumber": 0, '
        '"Name": "string", "Description": "string", "PseudonymTemplate": "string", '
        '"KeyfileKey": 0, "Deleted": true, "WorkspaceID": "string" } ] }',
    )

    KEYFILES_RESPONSE = (
        200,
        '{ "CreationDate": "2019-05-29T11:32:09.735Z", "SequenceNumber": 0, "Name": "string", '
        '"Description": "string", "PseudonymTemplate": "string", "KeyfileKey": 0, "Deleted": true,'
        '"WorkspaceID": "string" }',
    )

    KEYFILES_PSEUDONYMS_POST_RESPONSE = (  # response to successful post to Keyfiles/{KeyfileKey}/Pseudonyms
        201,
        '{"PseudonymLnkKey":167033,"KeyfileKey":26,"Pseudonym":"63bf2309-d280-44d0-914b-a74a25dfc56d",'
        '"Deleted":false,"Identifier":"Henk_Sjansen2","IdentitySource":"sjoerd_zelf"}',
    )

    KEYFILES_PSEUDONYMS_REIDENTIFY_RESPONSE = (  # response after successful re-identify of 2 pseudonyms
        200,
        '{"Count":2,"Page":1,"PageSize":20,"PageCount":1,"Data":[{"Name":"Pseudonyms","Type":null,'
        '"Keys":[166741,166742],"Action":4,"Values":["test",'
        '"test2"]},{"Name":"Identity","Type":["Identity","Identity"],'
        '"Keys":[166741,166742],"Action":4,"Values":["sjoerd_kerkstra","secret"]},{"Name":"Identity Source",'
        '"Type":["IdentitySource","IdentitySource"],"Keys":[166741,166742],"Action":4,"Values":["PatientID",'
        '"PatientID"]}]}',
    )

    # response after re-identify for unknown pseudonyms (empty response)
    KEYFILES_PSEUDONYMS_REIDENTIFY_NON_EXISTENT_RESPONSE = (
        200,
        '{"Count": 0, "Page": 1, "PageSize": 500, "PageCount": 1, "Data": ['
        '{"Name": "Pseudonyms", "Type": null, "Keys": [], "Action": 4,'
        '"Values": []},'
        '{"Name": "Identity", "Type": ["text"], "Keys": [], "Action": 4,'
        '"Values": []},'
        '{"Name": "Identity Source", "Type": ["text"], "Keys": [], "Action": 4,'
        '"Values": []}]}',
    )

    # response after re-identify where one pseudonym is known
    KEYFILES_PSEUDONYMS_REIDENTIFY_EXISTENT_RESPONSE = (
        200,
        '{"Count":1,"Page":1,"PageSize":500,"PageCount":1,"Data":[{'
        '"Name":"Pseudonyms","Type":null,"Keys":[3499406],"Action":4,"Values":['
        '"pseudo2"]},{"Name":"Identity","Type":["Identity"],"Keys":[3499406],'
        '"Action":4,"Values":["value2"]},{"Name":"Identity Source","Type":['
        '"IdentitySource"],"Keys":[3499406],"Action":4,"Values":["PatientID"]}]}',
    )

    GET_USER_BY_ID_RESPONSE = (  # Call to 'api/Users/{KeyFileKey}/Details'
        200,
        r'{"Count":1,"Page":1,"PageSize":20,"PageCount":1,"Data":[{"Name":"umcn\\SVC01234","Email":null,'
        '"DisplayName":null,"Department":null,"BaseRole":"NONE","UserKey":26,"Memberships":[{"Keyfile":26,'
        '"KeyfileName":"z428172_API_test","Role":"ROLE_NONHUMAN_STANDARD_WITH_REIDENTIFICATION_RIGHTS",'
        '"NiceRole":"nonhuman standard with reidentification rights","Deleted":false}],"More":true,"Deleted":false}]}',
    )

    GET_USERS_FOR_KEYFILE_RESPONSE = (  # response after successful GET to Keyfiles/{KeyfileKey}/Users
        200,
        r'{ "Count": 2, "Page": 1, "PageSize": 20, "PageCount": 1, "Data": [ { "Name": "umcn\\SVC01234", "Email":'
        r'"?", "DisplayName": "umcn\\SVC01234", "Department": "?", "BaseRole": "CREATE_KEYFILE", "UserKey": 26,'
        ' "Memberships": [ { "Keyfile": 26, "KeyfileName": "API_test", '
        '"Role": "ROLE_NONHUMAN_STANDARD_WITH_REIDENTIFICATION_RIGHTS", '
        '"NiceRole": "nonhuman standard with reidentification rights", "Deleted": false } ], '
        r'"More": false, "Deleted": false }, { "Name": "UMCN\\Z123456", "Email": "a.smith@radboudumc.nl", '
        '"DisplayName": "Smith, Arnold", "Department": "Radiologie en Nucleaire Geneeskunde",'
        ' "BaseRole": "NONE", "UserKey": 22, "Memberships": [ { "Keyfile": 26, "KeyfileName": "API_test",'
        ' "Role": "ROLE_KEYFILE_OWNER", "NiceRole": "key_file owner", "Deleted": false } ], "More": false,'
        ' "Deleted": false } ]}',
    )

    DEIDENTIFY_CREATE_JSONOUTPUT_TRUE = (  # response after posting 2 ids to  /Keyfiles/{KeyfileKey}}/Files/Deidentify'
        200,
        r'{"Headers":["Column 1","Pseudonyms (Stored in Keyfile https://pims.radboudumc.nl/Keyfiles/26/Details/26452)"]'
        r',"Data":[["","2326473b-3a35-448d-8901-b0fb1f983aff"],["","40f5e7a3-688e-4654-b432-2d0b8138e8b6"]]}',
    )

    DEIDENTIFY_CREATE_JSONOUTPUT_TRUE_INVALID = (  # same as above, but returns multiple pseudonyms per identity.
        200,
        r'{"Headers":["Column 1","Pseudonyms (Stored in Keyfile https://pims.radboudumc.nl/Keyfiles/26/Details/26452)"]'
        r',"Data":[["","2326473b-3a35-448d-8901-b0fb1f983aff"],["","40f5e7a3-688e-4654-b432-2d0b8138e8b6", "extra!"]]}',
    )

    DEIDENTIFY_FAILED_TO_INSERT = (  # Trying to re-insert an existing pseudonym
        500,
        '{"Message":"Row #3: Failed to insert pseudonyms because one of the '
        "pseudonyms already exists in the target keyfile with a different "
        "identifier (or the identifier is already associated with another "
        "pseudonym). Culprit(s) are one or more of the following pseudonyms: "
        "pseudo1, pseudo2. \r\nProcess aborted. See Action #1159690 for any "
        'completed progress (already processed 0 rows).\r\n"}',
    )
