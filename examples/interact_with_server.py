"""Just some basic interactions with a PIMS server

To run this example, make sure you have a PIMS keyfile and have set the
environment variables
PIMS_CLIENT_USER
PIMS_CLIENT_PASSWORD
"""
from pimsclient.server import PIMSServer
from pimsclient.swagger import KeyFiles, Users

api = PIMSServer("https://pims.radboudumc.nl/api")
session = api.get_session()

keyfiles = KeyFiles(session=session)
keyfile = keyfiles.get(key=26)
print(keyfile)

users = Users(session=session)
user = users.get(key=26)
print(user)

all_mine = keyfiles.get_all(user=user)
print(all_mine)
