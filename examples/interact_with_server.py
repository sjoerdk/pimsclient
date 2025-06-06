import logging
from pathlib import Path

from pimsclient.auth.msal import quick_auth_with_cert
from pimsclient.client import AuthenticatedClient
from pimsclient.keyfile import KeyFile
from pimsclient.server import PIMSServer

logging.basicConfig(level=logging.INFO)

with open("/home/sjoerd/ticketdata/G00109/certificate.pem") as f:
    public_key = f.read()

session = quick_auth_with_cert(
    requester_id="1789e794-241c-473b-9921-30e05d284b01",
    requester_public_key=public_key,
    requester_private_key_file=Path("/tmp/priv"),
    pims_id="4683335c-4d2c-419a-90e0-418ef25f8a16",
    radboud_id="b208fe69-471e-48c4-8d87-025e9b9a157f",
)

client = AuthenticatedClient(session=session)
server = PIMSServer(url="https://pims.radboudumc.nl/api/v0")
keyfile = KeyFile.init_from_id(keyfile_id=634, client=client, server=server)

print(f"Connected to {keyfile}")
