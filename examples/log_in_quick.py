"""How to authenticate with Azure AD

Does not explain, just shows the quickest way. For more info see example
'log_in_with_certificate'.
"""

from pathlib import Path

from requests import Session

from pimsclient.auth.msal import MSALAuth

session = Session()
session.auth = MSALAuth(
    requester_id="1789e794-241c-473b-9921-30e05d284b01",
    requester_public_key=open("/tmp/public_key").read(),
    requester_private_key_file=Path("/tmp/priv"),
    pims_id="4683335c-4d2c-419a-90e0-418ef25f8a16",
    radboud_id="b208fe69-471e-48c4-8d87-025e9b9a157f",
)

response = session.get("https://some_pims_server.nl/keyfiles", verify=False)
print(response)
