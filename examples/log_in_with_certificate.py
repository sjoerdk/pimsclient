"""How to authenticate with Azure AD

To authenticate with azure and then use an API endpoint you need five different
pieces of information. Coming from a user/password perspective this can be
bewildering. This example show the different elements of the authentication.

If you don't care about this and/or want the shortest login code, see example
`log_in_quick`
"""

import logging
from pathlib import Path

from pimsclient.auth.msal import API, Application, Tenant, SSLKeyPair

# ======================= define objects required for authentication ================
with open("/home/sjoerd/ticketdata/G00109/certificate.pem") as f:
    certificate = SSLKeyPair(
        public_key=f.read(),
        private_key_file=Path("/tmp/priv"),
        description="IDIS",
    )

idis = Application(
    msal_id="1789e794-241c-473b-9921-30e05d284b01",
    name="IDIS",
    certificate=certificate,
)

pims = API(
    msal_id="4683335c-4d2c-419a-90e0-418ef25f8a16",
    name="PIMS_v0",
    base_url="https://pims.radboudumc.nl/api/v0",
)

radboud = Tenant(
    msal_id="b208fe69-471e-48c4-8d87-025e9b9a157f", name="Radboudumc"
)

# ========================= actually authenticate ===================================

logging.basicConfig(level=logging.INFO)
s = radboud.obtain_authorized_session(request_for=idis, to_access=pims)

url = pims.base_url + "/keyfiles"
response = s.get(url)
print(response)

logging.info("done")
