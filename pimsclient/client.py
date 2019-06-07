# -*- coding: utf-8 -*-

""" Classes and functions for working with the PIMS pseudonym management system.

This module adds one level above the Swagger level, abstracting away details and making it easy to work with multiple
types of pseudonym under a single project description
"""
from pimsclient.server import PIMSServer
from pimsclient.swagger import Identifier, Pseudonym, KeyFiles, Users, Key


def connect(pims_url, pims_key_file_id):
    """Convenience function to create a project connected to a keyfile

    Parameters
    ----------
    pims_url: str
        url to PIMS swagger API
    pims_key_file_id: int
        PIMS id for the keyfile you are trying to link to

    Returns
    -------
    Project
        A project connected to keyfile

    """
    connection = PIMSConnection(session=PIMSServer(pims_url).get_session())
    return Project(key_file_id=pims_key_file_id, connection=connection)


class Project:
    """Main object for PIMS client. A project holds all pseudonymization information for one or more value_type(s) of
    identifiers. It stores all its data in a single PIMS keyfile.

    """

    def __init__(self, key_file_id, connection=None):
        """Create a project

        Parameters
        ----------
        key_file_id: int
            PIMS db id of keyfile that this project is linked to
        connection: PIMSConnection
            Connection to communicate over for this project
        """
        self.key_file_id = key_file_id
        self._connection = connection
        self._key_file = None
        self.factory = KeyTypeFactory()

    def __str__(self):
        return (
            f"Project for keyfile {self.key_file_id} over connection {self.connection}"
        )

    @property
    def connection(self):
        if self._connection:
            return self._connection
        else:
            raise NoConnectionException(
                "This project is not connected to any PIMS server"
            )

    def get_key_file(self):
        """Caches keyfile got from PIMS locally"""
        if not self._key_file:
            self._key_file = self.connection.get_key_file(key=self.key_file_id)
        return self._key_file

    def get_name(self):
        return self.get_key_file().name

    def pseudonymize(self, identifiers):
        """Get a pseudonym from PIMS for each identifier in list

        Parameters
        ----------
        identifiers: List[TypedIdentifier]
            identifiers to pseudonymize

        Returns
        -------
        List[TypedKey]
            Each identifier mapped to PIMS pseudonym

        """
        keys = self.connection.pseudonymize(
            key_file=self.get_key_file(), identifiers=identifiers
        )

        return [self.factory.create_typed_key(x) for x in keys]

    def reidentify(self, pseudonyms):
        """Get identifiers for each pseudonym in list

        Parameters
        ----------
        pseudonyms: List[TypedPseudonym]
            list of pseudonyms to process

        Returns
        -------
        List[TypedKey]
            Pseudonym mapped to identifier if found. If a pseudonym is not found in PIMS it is omitted from list

        """
        keys = self.connection.reidentify(key_file=self.get_key_file(), pseudonyms=pseudonyms)
        return [self.factory.create_typed_key(x) for x in keys]


class PIMSConnection:
    def __init__(self, session):
        """A logged in session to a PIMS server. Main way in client lib of interacting with PIMS

        Parameters
        ----------
        session: PIMSSession
            session to use for communicating with PIMS

        """
        self.session = session
        self.key_files = KeyFiles(session=self.session)
        self.users = Users(session=self.session)

    def get_key_file(self, key):
        """Get specific key file

        Parameters
        ----------
        key: int or str
            key for the key_file to get

        Returns
        -------
        KeyFile
        """
        return self.key_files.get(key)

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
        return self.key_files.pseudonymize_legacy(
            key_file=key_file, identifiers=identifiers
        )

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
        return self.key_files.reidentify(key_file=key_file, pseudonyms=pseudonyms)


class ValueTypes:
    """Types of identifiers or pseudonyms in PIMS.

    Needed as a patientID should be treated differently then a SeriesInstanceUID. Different patterns for generating for
    example.

    Whenever a DICOM tag is pseudonymized, the DICOM tag name is used as value_type descriptor.

    See for example name
    https://www.sno.phy.queensu.ca/~phil/exiftool/TagNames/DICOM.html
    """

    PATIENT_ID = "PatientID"
    STUDY_INSTANCE_UID = "StudyInstanceUID"
    SERIES_INSTANCE_UID = "SeriesInstanceUID"
    SOP_INSTANCE_UID = "SOPInstanceUID"
    NOT_SET = "NOT_SET"

    all = [PATIENT_ID, STUDY_INSTANCE_UID, SERIES_INSTANCE_UID, SOP_INSTANCE_UID]


class TypedIdentifier(Identifier):
    """An identifier with a specific value_type.

    """

    value_type = ValueTypes.NOT_SET

    def __init__(self, value):
        super().__init__(value=value, source=self.value_type)

    @property
    def value_type(self):
        """In swagger layer value_type is saved as 'source'. Expose this here as value_type because it fits the concepts
        better

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
    """ Designates a single slice in a DICOM file
    """

    value_type = ValueTypes.SOP_INSTANCE_UID


class TypedPseudonym(Pseudonym):
    """A pseudonym with a specific value_type.

    """

    value_type = ValueTypes.NOT_SET

    def __init__(self, value):
        super().__init__(value=value)
        self.value_type = self.value_type

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


class NoConnectionException(Exception):
    pass


class TypedKey(Key):
    """An identity-pseudonym mapping where both have the same value_type

    """

    def __init__(self, identifier, pseudonym):
        """Create a typed Key

        Parameters
        ----------
        identifier: TypedIdentifier
            Real identifier, like 'Yen Hu'
        pseudonym: TypedPseudonym
            Pseudonym used for the identifyer, like 'Case3'
        """
        super().__init__(identifier, pseudonym)

    def __str__(self):
        return f'Key <{self.value_type}>: {self.pseudonym.value}'

    @property
    def value_type(self):
        """According to convention, source is used to hold value_type information"""
        return self.identifier.source


class KeyTypeFactory:
    """For casting swagger objects to typed objects

    """

    identifier_class_map = {
        x.value_type: x
        for x in [PatientID, StudyInstanceUID, SeriesInstanceUID, SOPInstanceUID]
    }
    pseudonym_class_map = {
        x.value_type: x
        for x in [
            PseudoPatientID,
            PseudoStudyInstanceUID,
            PseudoSeriesInstanceUID,
            PseudoSOPInstanceUID,
        ]
    }

    def create_typed_key(self, key):
        """Take given swagger.Key and cast to typed key

        Parameters
        ----------
        key: Key

        Raises
        ------
        TypedKeyFactoryException
            If key cannot be cast to a known type

        Returns
        -------
        TypedKey

        """
        identifier = self.create_typed_identifier(identifier=key.identifier)
        pseudonym = self.create_typed_pseudonym(pseudonym=key.pseudonym, value_type=identifier.value_type)

        return TypedKey(identifier=identifier, pseudonym=pseudonym)

    def create_typed_identifier(self, identifier):
        """Cast identifier to typed version

        Parameters
        ----------
        identifier: Identifier

        Raises
        ------
        TypedKeyFactoryException
            If identifier cannot be cast to a known type

        Returns
        -------
        TypedIdentifier

        """
        try:
            identifier_class = self.identifier_class_map[identifier.source]
            return identifier_class(identifier.value)
        except KeyError:
            msg = f'Unknown value type "{identifier.source}". Known types: {list(self.identifier_class_map.keys())}'
            raise TypedKeyFactoryException(msg)

    def create_typed_pseudonym(self, pseudonym, value_type):
        """Cast identifier to typed version

        Parameters
        ----------
        pseudonym: Pseudonym
            pseudonym to cast
        value_type: str
            one of ValueTypes

        Raises
        ------
        TypedKeyFactoryException
            If pseudonym cannot be cast to a known type

        Returns
        -------
        TypedPseudonym

        """
        try:
            identifier_class = self.pseudonym_class_map[value_type]
            return identifier_class(pseudonym.value)
        except ValueError:
            msg = f'Unknown value type {pseudonym.source}. Known types: {list(self.pseudonym_class_map.keys())}'
            raise TypedKeyFactoryException(msg)


class TypedKeyFactoryException(Exception):
    pass