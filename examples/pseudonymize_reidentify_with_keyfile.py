"""Use a KeyFile to work with pseudonyms"""
import logging
from pathlib import Path

from requests import Session

from pimsclient.auth.msal import MSALAuth
from pimsclient.client import AuthenticatedClient
from pimsclient.core import (
    PatientID,
    PseudoPatientID,
    PseudoStudyInstanceUID,
    StudyInstanceUID,
)
from pimsclient.keyfile import KeyFile
from pimsclient.server import PIMSServer

logging.basicConfig(level=logging.DEBUG)

with open("/home/sjoerd/ticketdata/G00109/certificate.pem") as f:
    public_key = f.read()

session = Session()
session.auth = MSALAuth(
    requester_id="1789e794-241c-473b-9921-30e05d284b01",
    requester_public_key=public_key,
    requester_private_key_file=Path("/tmp/priv"),
    pims_id="4683335c-4d2c-419a-90e0-418ef25f8a16",
    radboud_id="b208fe69-471e-48c4-8d87-025e9b9a157f",
)

client = AuthenticatedClient(session=session)
server = PIMSServer(url="https://pims.radboudumc.nl/api/v0")
keyfile = KeyFile.init_from_id(keyfile_id=49, client=client, server=server)

# I have some patientID's I want to pseudonymize with PIMS
print("Pseudonymizing some patientIDs: ")
keys1 = keyfile.pseudonymize(
    [PatientID("g5123"), PatientID("d5123"), StudyInstanceUID("d5123")]
)
print("identities:")
print([str(x.identifier) + " - " + str(x) for x in keys1])

# extract the pseudonyms to use as example in next step
pseudo_patient_name1 = keys1[0].pseudonym.value
pseudo_patient_name2 = keys1[1].pseudonym.value
pseudo_study_instance_uid = keys1[2].pseudonym.value

# Next step, Other way around: I found some pseudonymized patientID's. What was
# the original ID?
print("Reidentifying the pseudonyms:")
keys2 = keyfile.reidentify(
    [
        PseudoPatientID(pseudo_patient_name1),
        PseudoPatientID(pseudo_patient_name2),
        PseudoStudyInstanceUID(pseudo_study_instance_uid),
    ]
)
print([str(x) + " - " + str(x.identifier) for x in keys2])
