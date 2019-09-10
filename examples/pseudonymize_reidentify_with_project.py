"""Pseudonymize and re-identify using the hopefully more understandable

"""
from pimsclient.client import connect, PatientID, PseudoPatientID

# Create a project connected to a certain PIMS key file
project = connect('https://pims.radboudumc.nl/api', pims_key_file_id=44)
print(project.get_pims_pseudonym_template())

# I have some patientID's I want to pseudonymize with PIMS
print("Pseudonymizing some patientIDs: ")
keys1 = project.pseudonymize([PatientID('5123'), PatientID('5124'), PatientID('5125')])
print([str(x.identifier) + " - " + str(x) for x in keys1])

# extract the pseudonyms to use as example in next step
pseudo_patient_name1 = keys1[0].pseudonym.value
pseudo_patient_name2 = keys1[1].pseudonym.value
pseudo_patient_name3 = keys1[2].pseudonym.value

# Next step, Other way around: I found some pseudonymized patientID's. What was the original ID?
print("Reidentifying the pseudonyms:")
keys2 = project.reidentify([PseudoPatientID(pseudo_patient_name1),
                            PseudoPatientID(pseudo_patient_name2),
                            PseudoPatientID(pseudo_patient_name3)])
print([str(x) + " - " + str(x.identifier) for x in keys2])

