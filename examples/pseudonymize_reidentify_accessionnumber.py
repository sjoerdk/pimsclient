"""Pseudonymize and re-identify using the hopefully more understandable

To run this example, make sure you have a PIMS keyfile and have set the
environment variables
PIMS_CLIENT_USER
PIMS_CLIENT_PASSWORD
"""

from pimsclient.client import AccessionNumber, PseudoAccessionNumber, connect

# Create a project connected to a certain PIMS key file
project = connect("https://pims.radboudumc.nl/api", pims_key_file_id=49)
print(project.get_pims_pseudonym_template())

print("Pseudonymizing some accession numbers: ")
keys1 = project.pseudonymize(
    [AccessionNumber("DVD132424.1231231"), AccessionNumber("1234567.12345678")]
)
print([str(x.identifier) + " - " + str(x) for x in keys1])

# extract the pseudonyms to use as example in next step
pseudo1 = keys1[0].pseudonym.value
pseudo2 = keys1[1].pseudonym.value

print("Reidentifying the pseudonyms:")
keys2 = project.reidentify(
    [PseudoAccessionNumber(pseudo1), PseudoAccessionNumber(pseudo2)]
)
print([str(x) + " - " + str(x.identifier) for x in keys2])
