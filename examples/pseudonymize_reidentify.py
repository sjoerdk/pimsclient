"""Connect to a PIMS server, anonymize some identifyers, then re-identify the pseudonyms you get back

"""
from pimsclient.server import PIMSServer
from pimsclient.swagger import KeyFiles, Identifier

api = PIMSServer('https://pims.radboudumc.nl/api')
session = api.get_session()
keyfiles = KeyFiles(session=session)

key_file = keyfiles.get(key=26)
#print(f"= Pseudonymizing some identifyers in {key_file} ==================")
keys = keyfiles.pseudonymize(key_file=key_file, identifiers=[Identifier('kees2', 'PatientID'),
                                                             Identifier('henk1', 'PatientID')])

#[print(y) for y in [f"{x.pseudonym} -> {x.identifier}" for x in keys]]


#print(f"= Reidentifying in {key_file} ================")
#keyfiles.reidentify(key_file=key_file, pseudonyms=[x.pseudonym for x in keys])
#[print(y) for y in [f"{x.identifier} -> {x.pseudonym}" for x in keys]]

