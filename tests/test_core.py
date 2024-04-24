import pytest

from pimsclient.core import Key, KeyTypeFactory
from pimsclient.exceptions import TypedKeyFactoryError
from tests.factories import IdentifierFactory, PseudonymFactory


def test_typed_key_factory_exception():
    """Trying to create a typed key for an unknown type should fail"""
    key = Key(
        identifier=IdentifierFactory(source="UNKNOWN"),
        pseudonym=PseudonymFactory(),
    )

    with pytest.raises(TypedKeyFactoryError):
        KeyTypeFactory().create_typed_key(key)

    with pytest.raises(TypedKeyFactoryError):
        KeyTypeFactory().create_typed_pseudonym(
            PseudonymFactory(), value_type="UNKNOWN"
        )


@pytest.mark.parametrize(
    "value_type",
    ["PatientID", "StudyInstanceUID", "SeriesInstanceUID", "SOPInstanceUID"],
)
def test_typed_key_factory(value_type):
    """Creating typed keys for these value types should work"""
    key = Key(
        identifier=IdentifierFactory(source=value_type),
        pseudonym=PseudonymFactory(),
    )

    typed_key = KeyTypeFactory().create_typed_key(key)
    assert typed_key.value_type == value_type
