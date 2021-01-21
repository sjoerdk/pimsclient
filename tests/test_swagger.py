from pimsclient.client import PseudoPatientID
from pimsclient.swagger import KeyFile, User, KeyFiles, Users, Identifier
from tests.factories import (
    UserFactory,
    KeyFileFactory,
    RequestsMockResponseExamples,
    PseudonymFactory,
    IdentifierFactory,
    PatientIDFactory,
    PseudoPatientIDFactory,
)


def test_swagger_user():
    user = UserFactory()
    as_dict = user.to_dict()

    reconstructed = User.from_dict(as_dict)
    assert reconstructed.email == user.email
    assert reconstructed.name == user.name
    assert reconstructed.key == user.key


def test_swagger_keyfile():
    keyfile = KeyFileFactory()
    as_dict = keyfile.to_dict()

    reconstructed = KeyFile.from_dict(as_dict)
    assert reconstructed.pseudonym_template == keyfile.pseudonym_template
    assert reconstructed.description == keyfile.description
    assert reconstructed.name == keyfile.name
    assert reconstructed.key == keyfile.key


def test_keyfiles_entrypoint(mock_pims_session):
    """Get some object from entrypoint, server is mocked and returning mocked
    responses
    """
    mock_pims_session.session.set_response_tuple(
        RequestsMockResponseExamples.KEYFILES_FORUSER_RESPONSE
    )
    entrypoint = KeyFiles(mock_pims_session)

    keyfiles = entrypoint.get_all(user=UserFactory())
    assert len(keyfiles) == 1

    mock_pims_session.session.set_response_tuple(
        RequestsMockResponseExamples.KEYFILES_RESPONSE
    )
    keyfile = entrypoint.get(key=0)
    assert keyfile.name == "string"


def test_keyfiles_pseudonymize(mock_pims_session):
    """Get a pseudonym, mock server response"""
    mock_pims_session.session.set_response_tuple(
        RequestsMockResponseExamples.DEIDENTIFY_CREATE_JSONOUTPUT_TRUE
    )
    entrypoint = KeyFiles(mock_pims_session)
    keys = entrypoint.pseudonymize(
        key_file=KeyFileFactory(),
        identifiers=[
            Identifier(value="Jack de Boer", source="Test"),
            Identifier(value="Chris van Os", source="Test"),
        ],
    )
    assert len(keys) == 2
    assert keys[0].identifier.value == "Jack de Boer"


def test_keyfiles_pseudonymize_different_sources(mock_pims_session):
    """Get a pseudonym, mock server response. Two different sources should yield
    separate calls for each source
    """
    mock_pims_session.session.set_response_tuple(
        RequestsMockResponseExamples.DEIDENTIFY_CREATE_JSONOUTPUT_TRUE
    )
    entrypoint = KeyFiles(mock_pims_session)
    entrypoint.pseudonymize(
        key_file=KeyFileFactory(),
        identifiers=[
            Identifier(value="Jack de Boer", source="Test"),
            Identifier(value="Sarah Toh", source="Test_2"),
        ],
    )
    assert mock_pims_session.session.requests_mock.post.call_count == 2


def test_keyfiles_pseudonymize_chunk_size(mock_pims_session):
    """In live testing the PIMS server was found not to be able to handle API
    requests with more then 1000 items Check the chunking system to work around
    this
    """

    mock_pims_session.session.set_response_tuple(
        RequestsMockResponseExamples.DEIDENTIFY_CREATE_JSONOUTPUT_TRUE
    )
    entrypoint = KeyFiles(mock_pims_session)
    _ = entrypoint.pseudonymize(
        key_file=KeyFileFactory(),
        identifiers=[PatientIDFactory() for _ in range(2000)],
    )
    values_posted = mock_pims_session.session.requests_mock.post.mock_calls[0][2][
        "json"
    ][0]["values"]
    assert len(values_posted) <= 1001


def test_keyfiles_reidentify(mock_pims_session):
    mock_pims_session.session.set_response_tuple(
        RequestsMockResponseExamples.KEYFILES_PSEUDONYMS_REIDENTIFY_RESPONSE
    )
    entrypoint = KeyFiles(mock_pims_session)

    keys = entrypoint.reidentify(
        key_file=KeyFileFactory(),
        pseudonyms=[PseudoPatientID(value="test"), PseudoPatientID(value="test2")],
    )

    assert len(keys) == 2
    assert keys[0].identifier.source == "PatientID"


def test_keyfiles_reidentify_chunked(mock_pims_session):
    mock_pims_session.session.set_response_tuple(
        RequestsMockResponseExamples.KEYFILES_PSEUDONYMS_REIDENTIFY_RESPONSE
    )
    entrypoint = KeyFiles(mock_pims_session)

    _ = entrypoint.reidentify(
        key_file=KeyFileFactory(),
        pseudonyms=[PseudoPatientIDFactory() for _ in range(2000)],
    )
    reidentified_items = mock_pims_session.session.requests_mock.post.mock_calls[0][2][
        "params"
    ]["items"]
    assert len(reidentified_items) <= 501


def test_keyfiles_get_users(mock_pims_session):
    mock_pims_session.session.set_response_tuple(
        RequestsMockResponseExamples.GET_USERS_FOR_KEYFILE_RESPONSE
    )
    entrypoint = KeyFiles(mock_pims_session)

    users = entrypoint.get_users(key_file=KeyFileFactory())

    assert len(users) == 2
    assert users[1].key == 22


def test_users_get_by_id(mock_pims_session):
    mock_pims_session.session.set_response_tuple(
        RequestsMockResponseExamples.GET_USER_BY_ID_RESPONSE
    )
    entrypoint = Users(mock_pims_session)

    user = entrypoint.get(key=1)

    assert user.name == "umcn\\SVC01234"


def test_string_reprs():
    """Getting coverage up a bit"""
    all_strings = (
        f"{UserFactory()}{KeyFileFactory()}{PseudonymFactory()}{IdentifierFactory()}"
    )
    assert all_strings != ""  # Or actually, assert nothing crashed
