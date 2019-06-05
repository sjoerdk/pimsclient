# -*- coding: utf-8 -*-

""" Classes and function for working with the PIMS pseudonym management system.

Pims uses the 'key_file' as its main object. A key_file is a table of original IDs and connected pseudonyms. Each key_file
has a single template for generating new pseudonyms.

This module adds one level above the PIMS level, making it possible to maintain multiple types of pseudonym under a
single project description
"""


class Identifier:
    def __init__(self, value, source):
        """A real patientID, StudyInstance or the like, with a source

        Parameters
        ----------
        value: str
            PatientID, StudyInstance or whatever should be pseudonymized
        source: str
            Source for this value, like the hospital where the PatientID is used. Used for disambiguation
        """
        self.value = value
        self.source = source

    def __str__(self):
        return f"Identifier '{self.value}' (source:'{self.source}')"

    def to_dict(self):
        return {"identifier": self.value, "identity_source": self.source}


class Pseudonym:
    def __init__(self, value):
        """A pseudonym, for an actual identifyer.

        Parameters
        ----------
        value: str
            The value of this pseudonym, like 'Patient1' or 'Case_23'
        """
        self.value = value

    def __str__(self):
        return f"Pseudonym '{self.value}'"


class Key:
    def __init__(self, identifier, pseudonym):
        """Combines an identifier with a pseudonym. The main constituent of a key file

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
    def init_from_strings(cls, pseudonym, identity, identity_source):
        """Creates a Key from string-only input arguments. For convenience

        Parameters
        ----------
        pseudonym: str
        identity: str
        identity_source: str

        Returns
        -------
        Key
        """
        return cls(
            identifier=Identifier(value=identity, source=identity_source),
            pseudonym=Pseudonym(value=pseudonym),
        )

    def __str__(self):
        return f"Key {self.pseudonym.value}"


# TODO: create second layer. classes: Project StudyInstanceUID, PatientName, etc, all with their own key_file

