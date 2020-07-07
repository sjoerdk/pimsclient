=====
Usage
=====

To use pimsclient in a project

.. code-block:: python

    from pimsclient.client import connect, PatientID, PseudoPatientID

    # Create a project connected to a certain PIMS key file
    project = connect('https://pims.radboudumc.nl/api',
                       pims_key_file_id=26)

    # I have some patientIDs I want to pseudonymize with PIMS
    keys = project.pseudonymize([PatientID('1234'),
                                 PatientID('5678'),
                                 PatientID('9012')])

    # I found some pseudo patientIDs. What was the original ID?
    keys = project.reidentify([PseudoPatientID('Patient1'),
                               PseudoPatientID('Patient2'),
                               PseudoPatientID('Patient3')])


Credentials
-----------
Should be set in the environment using the keys:

    `PIMS_CLIENT_USER`

    `PIMS_CLIENT_PASSWORD`



