"""Connect to a PIMS server, anonymize some identifyers, then re-identify the pseudonyms you get back

"""
from pimsclient.client import connect, PatientID, PseudoPatientID

# Create a project connected to a certain PIMS key file
project = connect('https://pims.radboudumc.nl/api', pims_key_file_id=26)

# I have some patientID's I want to pseudonymize with PIMS
keys = project.pseudonymize([PatientID('1234'), PatientID('5678'), PatientID('9012')])

# Other way around: I found some pseudonymized patientID's. What was the original ID?
keys = project.reidentify([PseudoPatientID('Patient1'),
                           PseudoPatientID('Patient2'),
                           PseudoPatientID('Patient3')])
