import pytest
from requests import session

from pimsclient.client import (
    AuthenticatedClient,
    IdentityNotFoundError,
    PseudonymTemplate,
)
from pimsclient.core import (
    PatientID,
    PseudoPatientID,
    PseudoSeriesInstanceUID,
    PseudoStudyInstanceUID,
    Pseudonym,
)
from pimsclient.exceptions import InvalidPseudonymTemplateError
from pimsclient.keyfile import KeyFile
from pimsclient.server import PIMSServer
from tests.factories import IdentifierFactory
from tests.mock_responses import MockUrls


def test_keyfile(mock_pims_responses):
    client = AuthenticatedClient(session=session())
    server = PIMSServer(url=MockUrls.SERVER_URL)
    keyfile = KeyFile.init_from_id(keyfile_id=49, client=client, server=server)
    assert keyfile


@pytest.fixture
def a_keyfile(mock_pims_responses) -> KeyFile:
    """A KeyFile instance with mocked response backend"""
    return KeyFile.init_from_id(
        keyfile_id=49,
        client=AuthenticatedClient(session=session()),
        server=PIMSServer(url=MockUrls.SERVER_URL),
    )


def test_anonymize(a_keyfile):
    """Test basic KeyFile methods. Reidentify needs specific query to make sure the
    mocked response matches and passes sanity checks
    """
    assert a_keyfile.pseudonymize([IdentifierFactory() for _ in range(3)])
    assert a_keyfile.reidentify(
        [
            Pseudonym(value="Patient000789", source="PatientID"),
            Pseudonym(value="Patient000786", source="PatientID"),
            Pseudonym(
                value="1.3.6.1.4.1.14519.5.2.1.9999.9999.79009"
                "944810124.60269537135357",
                source="StudyInstanceUID",
            ),
        ]
    )

    # What comes back from pims should match what was asked for. Keyfile should check
    # this. The mocked response will not contain a pseudonym 'not_in_mocked_response'
    with pytest.raises(IdentityNotFoundError):
        a_keyfile.reidentify(
            [Pseudonym(value="not_in_mocked_response", source="")]
        )


def test_check_existence(a_keyfile):
    """Basic run through existence checks. Just make sure no blatant issues are
    there
    """
    assert a_keyfile.exists(
        [
            PatientID("g5123"),
            PatientID("1234"),
            PseudoPatientID("Patient000786"),
        ]
    )


@pytest.mark.parametrize(
    "should_have, should_exist",
    [
        (
            [PseudoPatientID],
            [
                PseudonymTemplate(
                    template_string="#1.2,3.|N14|#.|N14",
                    pseudonym_class=PseudoStudyInstanceUID,
                )
            ],
        ),
        ([PseudoPatientID], []),
        ([PseudoPatientID, PseudoStudyInstanceUID], []),
        ([], []),
    ],
)
def test_project_assert_pseudonym_templates_working(
    a_keyfile, should_have, should_exist
):
    example_pims_template = (
        "Guid|:PatientID|#Patient|S6|:StudyInstanceUID|#1.2,3.|N14|#.|N14"
    )
    a_keyfile.info.pseudonymTemplate = example_pims_template

    a_keyfile.assert_pseudonym_templates(
        should_have_a_template=should_have, should_exist=should_exist
    )


@pytest.mark.parametrize(
    "should_have, should_exist",
    [
        (
            [PseudoPatientID],
            [
                PseudonymTemplate(
                    template_string="#youhavetohavethis",
                    pseudonym_class=PseudoStudyInstanceUID,
                )
            ],
        ),
        ([PseudoSeriesInstanceUID], []),
        ([PseudoPatientID, PseudoSeriesInstanceUID], []),
    ],
)
def test_project_assert_pseudonym_templates_failing(
    a_keyfile, should_have, should_exist
):
    example_pims_template = (
        "Guid|:PatientID|#Patient|S6|:StudyInstanceUID|#1.2,3.|N14|#.|N14"
    )
    a_keyfile.info.pseudonymTemplate = example_pims_template

    with pytest.raises(InvalidPseudonymTemplateError):
        a_keyfile.assert_pseudonym_templates(
            should_have_a_template=should_have, should_exist=should_exist
        )


def test_project_assert_pseudonym_templates_realistic(a_keyfile):
    """Test template checking with realistic values"""
    example_pims_template = (
        r"Guid|:PatientID|#Patient|S6|:StudyInstanceUID|#1.3.6.1.4.1.14519.5.2.1.9999.9999.|N14"
        r"|#.|N14|:SeriesInstanceUID|#1.3.6.1.4.1.14519.5.2.1.9999.9999.|N14|#.|N14|"
        r":SOPInstanceUID|#1.3.6.1.4.1.14519.5.2.1.9999.9999.|N14|#.|N14 "
    )
    a_keyfile.info.pseudonymTemplate = example_pims_template

    expected_templates = [
        PseudoPatientID,
        PseudoStudyInstanceUID,
        PseudoSeriesInstanceUID,
    ]
    a_keyfile.assert_pseudonym_templates(
        should_have_a_template=expected_templates, should_exist=[]
    )

    a_keyfile.info.pseudonymTemplate = "Guid"
    with pytest.raises(InvalidPseudonymTemplateError):
        a_keyfile.assert_pseudonym_templates(
            should_have_a_template=expected_templates, should_exist=[]
        )
