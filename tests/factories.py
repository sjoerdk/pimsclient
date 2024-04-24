import factory
from factory import fuzzy

from pimsclient.core import (
    Identifier,
    Key,
    PatientID,
    PseudoPatientID,
    Pseudonym,
    TypedKey,
    TypedPseudonym,
    ValueTypes,
)


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


class PseudonymFactory(factory.Factory):
    class Meta:
        model = Pseudonym

    value = factory.Sequence(lambda n: f"pseudonym{n}")


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
