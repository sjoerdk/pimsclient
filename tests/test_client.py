from unittest.mock import Mock

import pytest

from pimsclient.client import Project, KeyTypeFactory, TypedKeyFactoryException, NoConnectionException, \
    PIMSConnection, TypedPseudonym, PseudonymTemplate, PseudoPatientID, PseudoStudyInstanceUID, \
    InvalidPseudonymTemplateException, PseudoSeriesInstanceUID
from pimsclient.swagger import Key, PIMSSwaggerException
from tests.factories import IdentifierFactory, PseudonymFactory, TypedKeyFactory, RequestsMockResponseExamples, \
    KeyFileFactory, TypedPseudonymFactory, TypedIdentifierFactory


@pytest.fixture()
def mock_project():
    """A project with a mock connection that does not hit any server
    Instead calls to pseudonymize and reidentify will return a random list Key objects with valid value_types
    """

    mock_connection = Mock(spec=PIMSConnection)
    mock_connection.pseudonymize.return_value = [TypedKeyFactory() for _ in range(20)]
    mock_connection.reidentify.return_value = [TypedKeyFactory() for _ in range(20)]
    return Project(key_file_id=1, connection=mock_connection)


def test_project_no_connection():
    """Creating a project without a connection is possible, but calling server-hitting methods will fail"""
    project = Project(key_file_id=1, connection=None)
    with pytest.raises(NoConnectionException):
        project.reidentify(pseudonyms=[])

    with pytest.raises(NoConnectionException):
        project.pseudonymize(identifiers=[])


def test_project_functions(mock_project):
    keys = mock_project.pseudonymize(identifiers=[])
    assert len(keys) == 20

    keys = mock_project.reidentify(pseudonyms=[])
    assert len(keys) == 20


@pytest.mark.parametrize("should_have, should_exist",
                         [([PseudoPatientID], [PseudonymTemplate(template_string='#1.2,3.|N14|#.|N14',
                                                                 pseudonym_class=PseudoStudyInstanceUID)]),
                          ([PseudoPatientID], []),
                          ([PseudoPatientID, PseudoStudyInstanceUID], []),
                          ([], [])
                          ])
def test_project_assert_pseudonym_templates_working(mock_project, should_have, should_exist):
    example_pims_template = "Guid|:PatientID|#Patient|S6|:StudyInstanceUID|#1.2,3.|N14|#.|N14"
    mock_project.get_pims_pseudonym_template = lambda: example_pims_template

    mock_project.assert_pseudonym_templates(should_have_a_template=should_have,
                                            should_exist=should_exist)


@pytest.mark.parametrize("should_have, should_exist",
                         [([PseudoPatientID], [PseudonymTemplate(template_string='#youhavetohavethis',
                                                                 pseudonym_class=PseudoStudyInstanceUID)]),
                          ([PseudoSeriesInstanceUID], []),
                          ([PseudoPatientID, PseudoSeriesInstanceUID], []),
                          ])
def test_project_assert_pseudonym_templates_failing(mock_project, should_have, should_exist):
    example_pims_template = "Guid|:PatientID|#Patient|S6|:StudyInstanceUID|#1.2,3.|N14|#.|N14"
    mock_project.get_pims_pseudonym_template = lambda: example_pims_template

    with pytest.raises(InvalidPseudonymTemplateException):
        mock_project.assert_pseudonym_templates(should_have_a_template=should_have,
                                                should_exist=should_exist)




def test_typed_key_factory_exception():
    """Trying to create a typed key for an unknown type should fail"""
    key = Key(identifier=IdentifierFactory(source='UNKNOWN'), pseudonym=PseudonymFactory())

    with pytest.raises(TypedKeyFactoryException):
        KeyTypeFactory().create_typed_key(key)

    with pytest.raises(TypedKeyFactoryException):
        KeyTypeFactory().create_typed_pseudonym(PseudonymFactory(), value_type='UNKNOWN')


@pytest.mark.parametrize('value_type', ['PatientID',
                                        'StudyInstanceUID',
                                        'SeriesInstanceUID',
                                        'SOPInstanceUID'])
def test_typed_key_factory(value_type):
    """Creating typed keys for these value types should work"""
    key = Key(identifier=IdentifierFactory(source=value_type), pseudonym=PseudonymFactory())

    typed_key = KeyTypeFactory().create_typed_key(key)
    assert typed_key.value_type == value_type


def test_pimsconnection(mock_pims_session):
    connection = PIMSConnection(session=mock_pims_session)
    mock_pims_session.session.set_response_tuple(
        RequestsMockResponseExamples.DEIDENTIFY_CREATE_JSONOUTPUT_TRUE
    )
    connection.pseudonymize(key_file=KeyFileFactory(), identifiers=[IdentifierFactory()])

    mock_pims_session.session.set_response_tuple(
        RequestsMockResponseExamples.KEYFILES_PSEUDONYMS_REIDENTIFY_RESPONSE
    )
    connection.reidentify(key_file=KeyFileFactory(), pseudonyms=[PseudonymFactory()])


def test_str():
    project = Project(key_file_id=0, connection=Mock())
    string = f'{IdentifierFactory()}{project}{project.get_name()}{TypedKeyFactory()}{TypedIdentifierFactory}' \
        f'{TypedPseudonym(value="kees")}'

    assert string


def test_pseudonym_template():
    pid_template = PseudonymTemplate(template_string="#Patient|S6", pseudonym_class=PseudoPatientID)
    assert pid_template.as_pims_string() == ':PatientID|#Patient|S6'


def test_deidentify(mock_pims_session):
    connection = PIMSConnection(session=mock_pims_session)
    mock_pims_session.session.set_response_tuple(
        RequestsMockResponseExamples.DEIDENTIFY_CREATE_JSONOUTPUT_TRUE
    )
    identifiers = [IdentifierFactory(), IdentifierFactory()]
    keys = connection.pseudonymize(key_file=KeyFileFactory(), identifiers=identifiers)
    assert len(keys) == 2
    assert str(keys[0].identifier) == str(identifiers[0])

    mock_pims_session.session.set_response_tuple(
        RequestsMockResponseExamples.DEIDENTIFY_CREATE_JSONOUTPUT_TRUE_INVALID
    )

    with pytest.raises(PIMSSwaggerException) as e:
        connection.pseudonymize(key_file=KeyFileFactory(), identifiers=identifiers)
