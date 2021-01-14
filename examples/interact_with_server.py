"""Just some basic interactions with a PIMS server"""
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
