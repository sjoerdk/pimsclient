"""Data structures on top of the PIMS API that make it easier to work with
identities and pseudonyms. Abstracts away API details.
"""
from pimsclient.exceptions import TypedKeyFactoryError


class Identifier:
    def __init__(self, value, source):
        """A real patientID, StudyInstance or the like, with a source

        Parameters
        ----------
        value: str
            PatientID, StudyInstance or whatever should be pseudonymized
        source: str
            Source for this value, like the hospital where the PatientID is used.
            Used for disambiguation
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

    def __hash__(self):
        return hash((self.value, self.source))


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
        """Describe this Key like 'orginal -> pseudonym'"""
        return f"{self.identifier.value} -> {self.pseudonym.value}"


class ValueTypes:
    """Types of identifiers or pseudonyms in PIMS.

    Needed as a patientID should be treated differently then a SeriesInstanceUID.
    Different patterns for generating for
    example.

    Whenever a DICOM tag is pseudonymized, the DICOM tag name is used as value_type
    descriptor.

    See for example name
    https://www.sno.phy.queensu.ca/~phil/exiftool/TagNames/DICOM.html
    """

    PATIENT_ID = "PatientID"
    STUDY_INSTANCE_UID = "StudyInstanceUID"
    SERIES_INSTANCE_UID = "SeriesInstanceUID"
    SOP_INSTANCE_UID = "SOPInstanceUID"
    ACCESSION_NUMBER = "AccessionNumber"
    SALT = "Salt"
    NOT_SET = "NOT_SET"

    all = [
        PATIENT_ID,
        STUDY_INSTANCE_UID,
        SERIES_INSTANCE_UID,
        SOP_INSTANCE_UID,
        ACCESSION_NUMBER,
        SALT,
    ]


class TypedIdentifier(Identifier):
    """An identifier with a specific value_type"""

    def __init__(self, value):
        super().__init__(value=value, source=self.value_type)

    @property
    def value_type(self):
        """In swagger layer value_type is saved as 'source'. Expose this here as
        value_type because it fits the concepts better
        """
        return self.source

    def __str__(self):
        return f"{self.value_type}: {self.value}"


class PatientID(TypedIdentifier):
    value_type = ValueTypes.PATIENT_ID


class StudyInstanceUID(TypedIdentifier):
    value_type = ValueTypes.STUDY_INSTANCE_UID


class SeriesInstanceUID(TypedIdentifier):
    value_type = ValueTypes.SERIES_INSTANCE_UID


class SOPInstanceUID(TypedIdentifier):
    """Designates a single slice in a DICOM file"""

    value_type = ValueTypes.SOP_INSTANCE_UID


class AccessionNumber(TypedIdentifier):
    value_type = ValueTypes.ACCESSION_NUMBER


class SaltIdentifier(TypedIdentifier):
    value_type = ValueTypes.SALT


class TypedPseudonym(Pseudonym):
    """A pseudonym with a specific value_type"""

    value_type = ValueTypes.NOT_SET

    def __init__(self, value):
        super().__init__(value=value, source=self.value_type)

    def __str__(self):
        return f"Pseudo{self.value_type}: {self.value}"


class PseudoPatientID(TypedPseudonym):
    value_type = ValueTypes.PATIENT_ID


class PseudoStudyInstanceUID(TypedPseudonym):
    value_type = ValueTypes.STUDY_INSTANCE_UID


class PseudoSeriesInstanceUID(TypedPseudonym):
    value_type = ValueTypes.SERIES_INSTANCE_UID


class PseudoSOPInstanceUID(TypedPseudonym):
    value_type = ValueTypes.SOP_INSTANCE_UID


class PseudoAccessionNumber(TypedPseudonym):
    value_type = ValueTypes.ACCESSION_NUMBER


class PseudoSalt(TypedPseudonym):
    value_type = ValueTypes.SALT


class TypedKey(Key):
    """An identity-pseudonym mapping where both have the same value_type"""

    def __init__(self, identifier, pseudonym):
        """Create a typed Key

        Parameters
        ----------
        identifier: TypedIdentifier
            Real identifier, like 'Yen Hu'
        pseudonym: TypedPseudonym
            Pseudonym used for the identifier, like 'Case3'
        """
        super().__init__(identifier, pseudonym)

    def __str__(self):
        return f"Key <{self.value_type}>: {self.pseudonym.value}"

    @property
    def value_type(self):
        """According to convention, source is used to hold value_type information"""
        return self.identifier.source


class KeyTypeFactory:
    """For casting swagger objects to typed objects"""

    identifier_class_map = {
        x.value_type: x
        for x in [
            PatientID,
            StudyInstanceUID,
            SeriesInstanceUID,
            SOPInstanceUID,
            AccessionNumber,
            SaltIdentifier,
        ]
    }
    pseudonym_class_map = {
        x.value_type: x
        for x in [
            PseudoPatientID,
            PseudoStudyInstanceUID,
            PseudoSeriesInstanceUID,
            PseudoSOPInstanceUID,
            PseudoAccessionNumber,
            PseudoSalt,
        ]
    }

    def create_typed_key(self, key: Key) -> TypedKey:
        """Take given swagger. Key and cast to typed key

        Parameters
        ----------
        key: Key

        Raises
        ------
        TypedKeyFactoryError
            If key cannot be cast to a known type

        Returns
        -------
        TypedKey

        """
        identifier = self.create_typed_identifier(identifier=key.identifier)
        pseudonym = self.create_typed_pseudonym(
            pseudonym=key.pseudonym, value_type=identifier.value_type
        )

        return TypedKey(identifier=identifier, pseudonym=pseudonym)

    def create_typed_identifier(
        self, identifier: Identifier
    ) -> TypedIdentifier:
        """Cast identifier to typed version

        Parameters
        ----------
        identifier: Identifier

        Raises
        ------
        TypedKeyFactoryError
            If identifier cannot be cast to a known type

        Returns
        -------
        TypedIdentifier

        """
        try:
            identifier_class = self.identifier_class_map[identifier.source]
            return identifier_class(identifier.value)
        except KeyError as e:
            msg = (
                f'Unknown value type "{identifier.source}". Known types: '
                f"{list(self.identifier_class_map.keys())}"
            )
            raise TypedKeyFactoryError(msg) from e

    def create_typed_pseudonym(
        self, pseudonym: Pseudonym, value_type: str
    ) -> TypedPseudonym:
        """Cast identifier to typed version

        Parameters
        ----------
        pseudonym: Pseudonym
            pseudonym to cast
        value_type: str
            one of ValueTypes

        Raises
        ------
        TypedKeyFactoryError
            If pseudonym cannot be cast to a known type

        Returns
        -------
        TypedPseudonym

        """
        try:
            identifier_class = self.pseudonym_class_map[value_type]
            return identifier_class(pseudonym.value)
        except KeyError as e:
            msg = (
                f"Unknown value type {pseudonym.source}. Known types: "
                f"{list(self.pseudonym_class_map.keys())}"
            )
            raise TypedKeyFactoryError(msg) from e
