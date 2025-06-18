"""Mock responses

Based on live responses from a PIMS2 (2024-03-21)
"""
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Pattern, Union


class MockUrls:
    """For re-using across the code"""

    SERVER_URL = "https://testserver.test"


class MockIDs:
    """Object ids baked into mock responses. If you use these the responses will kind
    of match your requests
    """

    a_keyfile_id = 49


@dataclass
class MockResponse:
    """A fake server response that can be fed to response-mock easily"""

    url: Union[str, Pattern[str]]
    status_code: int = 200
    method: str = "GET"
    text: str = ""
    content: bytes = field(default_factory=bytes)
    json: Dict[str, Any] = field(default_factory=dict)
    reason: str = ""
    headers: Dict[str, str] = field(default_factory=dict)
    exc = None

    def as_dict(self):
        """Non-empty and non-None items as dictionary

        Facilitates use as keyword arguments. Like
        some_method(**MockResponse().as_dict())
        """
        return {x: y for x, y in self.__dict__.items() if y}


@dataclass
class MockResponseList:
    """Holds multiple MockResponses mapped to the same URL and Method.

    See [requests-mock reference](https://requests-mock.readthedocs.io/en/
    latest/response.html#response-lists)


    Notes
    -----
    MockResponse instances url and method parameters are overwritten by the
    responselists' fields when setting these responses
    """

    url: Union[str, Pattern[str]]
    method: str
    responses: List[MockResponse]


GET_KEYFILE_RESPONSE = MockResponse(
    url=re.compile(MockUrls.SERVER_URL + "/Keyfiles/.*"),
    status_code=200,
    method="GET",
    text='{"id":49,"name":"z428173_API_test2","pseudonymTemplate":"Guid|:PatientID|'
    "#Patient|S6|:StudyInstanceUID|#1.3.6.1.4.1.14519.5.2.1.9999.9999.|N14|#."
    "|N14|:SeriesInstanceUID|#1.3.6.1.4.1.14519.5.2.1.9999.9999.|N14|#.|N14|:"
    "SOPInstanceUID|#1.3.6.1.4.1.14519.5.2.1.9999.9999.|N14|#.|N14|:AccessionN"
    'umber|N7|#.|N8","creationDate":"2019-09-06T15:35:33.6406867","members":['
    '{"id":78,"keyfileID":49,"user":{"id":"9ffc9b24-f3a7-4d3a-bd90-4ae395d973'
    'ec","displayName":"Service principal: 1789e794-241c-473b-9921-30e05d284b'
    '01 (Image De-Identification Service (IDIS))","email":""},"roleDefinitio'
    'nID":"5bc1c1bf-5ef9-4f0d-b27b-fa503755a15a","activity":{"id":3050922}}],"'
    'deletable":false,"description":"Second test. First one is properly slugg'
    'ish now with 1.3M entries","sequenceNumber":792,"activity":{"id":305092'
    '2},"webhookStatus":"Disabled"}',
)

# Tests non-breaking change to json output
GET_KEYFILE_RESPONSE_WITH_CHANGE = MockResponse(
    url=re.compile(MockUrls.SERVER_URL + "/Keyfiles/.*"),
    status_code=200,
    method="GET",
    text='{"id":49,"name":"z428173_API_test2","pseudonymTemplate":"Guid|:PatientID|'
    "#Patient|S6|:StudyInstanceUID|#1.3.6.1.4.1.14519.5.2.1.9999.9999.|N14|#."
    "|N14|:SeriesInstanceUID|#1.3.6.1.4.1.14519.5.2.1.9999.9999.|N14|#.|N14|:"
    "SOPInstanceUID|#1.3.6.1.4.1.14519.5.2.1.9999.9999.|N14|#.|N14|:AccessionN"
    'umber|N7|#.|N8","creationDate":"2019-09-06T15:35:33.6406867","members":['
    '{"id":78,"keyfileID":49,"user":{"id":"9ffc9b24-f3a7-4d3a-bd90-4ae395d973'
    'ec","displayName":"Service principal: 1789e794-241c-473b-9921-30e05d284b'
    '01 (Image De-Identification Service (IDIS))","email":""},"roleDefinitio'
    'nID":"5bc1c1bf-5ef9-4f0d-b27b-fa503755a15a","activity":{"id":3050922}}],"'
    'deletable":false,"description":"Second test. First one is properly slugg'
    'ish now with 1.3M entries","sequenceNumber":792,"activity":{"id":305092'
    '2},"webhookStatus":"Disabled","headerCount":2, "rowCount":0}',
)

# Response below has a string id element (should be int) should break
GET_KEYFILE_RESPONSE_WITH_BREAKING_CHANGE = MockResponse(
    url=re.compile(MockUrls.SERVER_URL + "/Keyfiles/.*"),
    status_code=200,
    method="GET",
    text='{"id":"not an int","pseudonymTemplate":"Guid|:PatientID|'
    "#Patient|S6|:StudyInstanceUID|#1.3.6.1.4.1.14519.5.2.1.9999.9999.|N14|#."
    "|N14|:SeriesInstanceUID|#1.3.6.1.4.1.14519.5.2.1.9999.9999.|N14|#.|N14|:"
    "SOPInstanceUID|#1.3.6.1.4.1.14519.5.2.1.9999.9999.|N14|#.|N14|:AccessionN"
    'umber|N7|#.|N8","creationDate":"2019-09-06T15:35:33.6406867","members":['
    '{"id":78,"keyfileID":49,"user":{"id":"9ffc9b24-f3a7-4d3a-bd90-4ae395d973'
    'ec","displayName":"Service principal: 1789e794-241c-473b-9921-30e05d284b'
    '01 (Image De-Identification Service (IDIS))","email":""},"roleDefinitio'
    'nID":"5bc1c1bf-5ef9-4f0d-b27b-fa503755a15a","activity":{"id":3050922}}],"'
    'deletable":false,"description":"Second test. First one is properly slugg'
    'ish now with 1.3M entries","sequenceNumber":792,"activity":{"id":305092'
    '2},"webhookStatus":"Disabled","headerCount":2, "rowCount":0}',
)
# Responds to any deidentify call with three pseudonym-identity pairs
GET_DEIDENTIFY_RESPONSE = MockResponse(
    url=re.compile(
        MockUrls.SERVER_URL + "/Keyfiles/[0-9]+/Files/deidentify.*"
    ),
    status_code=200,
    method="POST",
    text='{"results":[{"values":["","",""],"pseudonymisationAction":"Identifier"},'
    '{"values":["","",""],"pseudonymisationAction":"IdentitySource"},{"values"'
    ':["Patient000789","Patient000786","1.3.6.1.4.1.14519.5.2.1.9999.9999.'
    '79009944810124.60269537135357"],"name":"Pseudonym","pseudonymisationActi'
    'on":"PseudonymOutput"}],"comments":""}',
)

# Responds to any deidentify call with three pseudonym-identity pairs
GET_REIDENTIFY_RESPONSE = MockResponse(
    url=re.compile(
        MockUrls.SERVER_URL + "/Keyfiles/[0-9]*/Identities/reidentify.*"
    ),
    status_code=200,
    method="POST",
    text='{"pseudonyms":{"page":0,"pageSize":20,"totalCount":3,"countComplete":true,'
    '"items":[{"id":5289924,"value":"d5123","identitySource":"PatientID",'
    '"pseudonym":"Patient000786","fields":[],"activity":{"id":3054186}},'
    '{"id":5290094,"value":"g5123","identitySource":"PatientID","pseudonym":'
    '"Patient000789","fields":[],"activity":{"id":3054186}},{"id":5290096,'
    '"value":"d5123","identitySource":"StudyInstanceUID","pseudonym":"1.3.6'
    '.1.4.1.14519.5.2.1.9999.9999.79009944810124.60269537135357","fields"'
    ':[],"activity":{"id":3054186}}]},"headers":[]}',
)

GET_IDENTITY_EXISTS_RESPONSE = MockResponse(
    url=re.compile(MockUrls.SERVER_URL + "/Keyfiles/[0-9]*/Identities/exists"),
    status_code=200,
    method="POST",
    text='{"g5123":true,"1234":false}',
)

GET_PSEUDONYM_EXISTS_RESPONSE = MockResponse(
    url=re.compile(MockUrls.SERVER_URL + "/Keyfiles/[0-9]*/Pseudonyms/exists"),
    status_code=200,
    method="POST",
    text='{"Patient000786":true}',
)
