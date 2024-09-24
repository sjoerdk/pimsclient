"""Authentication using the Microsoft Authentication library

https://github.com/AzureAD/microsoft-authentication-library-for-python

Notes
-----
For pimsclient there are two authentication situations
1) A user wants to use the pimsclient package in a python script they launch
   themselves
2) A stand-alone script or application wants to use pimsclient to access a pims server

There are two different workflows for this.
1) Use the 'on-behalf-of' (OBO) workflow. This requires the user to interactively log
into microsoft at some point during the script running

2) Use the `client credentials` authentication flow. We use ssl key pairs for this.

Only the second workflow is implemented at the moment
"""
from pathlib import Path
from typing import Dict

import requests
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.x509 import load_pem_x509_certificate
from msal import ConfidentialClientApplication
from requests.auth import AuthBase

from pimsclient.auth.exceptions import AuthError
from pimsclient.logs import get_module_logger

logger = get_module_logger("auth")


class SSLKeyPair:
    """A public and private SSL key

    Created this for cleaner definitions when using the microsoft MSAL lib.
    Tries to keep private key out of memory as much as possible

    Notes
    -----
    In Azure and the microsoft docs this is often called a `certificate`. In practice,
    it turns out no meta info is needed and the actual auth just needs a key pair
    """

    def __init__(
        self,
        public_key: str,
        private_key_file: Path,
        description: str = "",
    ):
        self.public_key = public_key
        self.private_key_file = private_key_file
        self.description = description

    def __str__(self):
        return f"SSL key pair '{self.description}'"

    def get_public_thumbprint(self):
        """Thumbprint for the public part of this key pair"""
        return (
            load_pem_x509_certificate(
                data=bytes(self.public_key, "UTF-8"), backend=default_backend()
            )
            .fingerprint(hashes.SHA1())
            .hex()
        )

    def as_msal_credential(self) -> Dict[str, str]:
        """Key pair in msal format

        specifically, format it so that it can be used as input for a
        msal.ConfidentialClientApplication class so that you can call
        msal.ConfidentialClientApplication.acquire_token_for_client() on it.

        Got this from inspecting msal 1.24.1
        """

        with open(self.private_key_file) as file:
            return {
                "private_key": file.read(),
                "thumbprint": self.get_public_thumbprint(),
                "public_certificate": self.public_key,
            }


class MSALObject:
    """A thing with a Microsoft ID"""

    def __init__(self, msal_id: str, name: str):
        self.msal_id = msal_id
        self.name = name

    def __str__(self):
        return f'{type(self)} "{self.name}" - {self.msal_id}'


class Application(MSALObject):
    def __init__(self, msal_id: str, name: str, certificate: SSLKeyPair):
        """An application in the microsoft auth world. Optionally with a certificate
        proving it is who it says it is.
        """
        super().__init__(msal_id, name)
        self.certificate = certificate


class API(MSALObject):
    def __init__(self, msal_id: str, name: str, base_url: str):
        """An API that has microsoft authentication"""
        super().__init__(msal_id, name)
        if base_url and base_url[-1] == "/":
            raise ValueError(
                f'Trailing slash in base_url "{base_url}" will cause '
                f"misery later. Please remove it."
            )
        self.base_url = base_url

    def as_scope(self):
        """If you want to indicate this api as the thing you want access to

        Not completely sure what the format is here. Pretty sure '.default' can be
        `access_as_user` and `.default` indicates that you want to log in as a
        'service principal' as opposed to 'log in on behalf of '.
        """
        return f"api://{self.msal_id}/.default"


class Tenant(MSALObject):
    """An organization that is paying microsoft to use their azure ecosystem.
    This organization can then ask microsoft to please authenticate users please.
    """

    # Used with authentication. Made this a constant to reduce init parameters
    AUTHORITY_URL = "https://login.microsoftonline.com"

    def obtain_authorized_session(
        self, request_for: Application, to_access: API
    ):
        """Obtain a requests session that is allowed to access the given API as
        the given application

        Returns
        -------
        requests.Session
            With valid access token
        """
        s = requests.Session()
        s.headers = {
            "authorization": "bearer "
            + self.get_sp_access_token(
                request_for=request_for, to_access=to_access
            )
        }

        return s

    def get_sp_access_token(self, request_for: Application, to_access: API):
        """Ask microsoft whether this tenant can request access to an API for the
        given application

        Returns
        -------
        str
        """
        logger.info(
            f"{self.name}: Attempting to obtain access token for "
            f"{request_for.name} to access {to_access.name}"
        )

        logger.debug(
            f"Using public key with thumbprint "
            f"'{request_for.certificate.get_public_thumbprint()}'"
        )

        app = ConfidentialClientApplication(
            client_id=request_for.msal_id,
            client_credential=request_for.certificate.as_msal_credential(),
            authority=f"{self.AUTHORITY_URL}/{self.msal_id}",
        )

        result = app.acquire_token_for_client(scopes=[to_access.as_scope()])

        if "access_token" in result:
            logger.info("Access token successfully acquired")
            return result["access_token"]
        else:
            logger.error("Unable to obtain access token")
            logger.error(
                f"Error was: {[(str(x),str(y)) for x,y in result.items()]}"
            )
            raise AuthError("Failed to obtain access token")


def quick_obtain_token(
    requester_id: str,
    requester_public_key: str,
    requester_private_key_file: Path,
    pims_id: str,
    radboud_id: str,
) -> str:
    """Get authenticated session token

    Parameters
    ----------
    requester_id
        microsoft auth id of the service principal (user) that you want to log in as
    requester_public_key
        authenticate with this public key
    requester_private_key_file
        prove you're the real requester with this
    pims_id
        microsoft auth id of the API you are trying to reach
    radboud_id
        microsoft auth id of the tenant which can authorize you to access

    Returns
    -------
    requests.Session
        authorized to use PIMS
    """

    requester = Application(
        msal_id=requester_id,
        name="requester",
        certificate=SSLKeyPair(
            public_key=requester_public_key,
            private_key_file=requester_private_key_file,
        ),
    )
    pims = API(msal_id=pims_id, name="PIMS", base_url="")
    radboud = Tenant(msal_id=radboud_id, name="Radboudumc")
    return radboud.get_sp_access_token(request_for=requester, to_access=pims)


def quick_auth_with_cert(
    requester_id: str,
    requester_public_key: str,
    requester_private_key_file: Path,
    pims_id: str,
    radboud_id: str,
):
    """Get authenticated session by just giving all the ids and locations in one go

    Parameters
    ----------
    requester_id
        microsoft auth id of the service principal (user) that you want to log in as
    requester_public_key
        authenticate with this public key
    requester_private_key_file
        prove you're the real requester with this
    pims_id
        microsoft auth id of the API you are trying to reach
    radboud_id
        microsoft auth id of the tenant which can authorize you to access

    Returns
    -------
    requests.Session
        authorized to use PIMS
    """

    requester = Application(
        msal_id=requester_id,
        name="requester",
        certificate=SSLKeyPair(
            public_key=requester_public_key,
            private_key_file=requester_private_key_file,
        ),
    )

    pims = API(msal_id=pims_id, name="PIMS", base_url="")

    radboud = Tenant(msal_id=radboud_id, name="Radboudumc")

    return radboud.obtain_authorized_session(
        request_for=requester, to_access=pims
    )


class MSALAuth(AuthBase):
    """Can obtain tokens with microsoft AD

    Raises
    ------
    PIMSClientError
        If logging in fails

    """

    def __init__(
        self,
        requester_id: str,
        requester_public_key: str,
        requester_private_key_file: Path,
        pims_id: str,
        radboud_id: str,
    ):
        """Can obtain tokens with microsoft AD

        Parameters
        ----------
        requester_id
            microsoft auth id of the service principal (user) that you want to log
            in as
        requester_public_key
            authenticate with this public key
        requester_private_key_file
            prove you're the real requester with this
        pims_id
            microsoft auth id of the API you are trying to reach
        radboud_id
            microsoft auth id of the tenant which can authorize you to access


        Raises
        ------
        PIMSClientError
            If logging in fails


        Returns
        -------
        requests.Session
            authorized to use PIMS
        """

        self.requester_id = requester_id
        self.requester_public_key = requester_public_key
        self.requester_private_key_file = requester_private_key_file
        self.pims_id = pims_id
        self.radboud_id = radboud_id
        self._bearer_token = None

    def response_hook(self, r, **kwargs):
        """Called before returning response. Try to log if not authenticated

        Parameters
        ----------
        r: Response

        """
        if r.status_code != 401:
            # not an access denied issue. I can't do anything here
            return r
        else:
            """Not logged in, try to obtain new session and retry request"""
            logger.debug("MSALAuth caught 401. Trying to re-obtain token")
            self._bearer_token = self.get_token()  # get new token

            # create a retry request with this new token
            retry_request = r.request.copy()
            retry_request.headers.update(self._bearer_token)
            retry_response = r.connection.send(retry_request, **kwargs)

            # make sure the retried response is now the official response
            retry_response.history.append(r)
            retry_response.request = retry_request

            return retry_response

    def get_token(self):
        token = quick_obtain_token(
            requester_id=self.requester_id,
            requester_public_key=self.requester_public_key,
            requester_private_key_file=self.requester_private_key_file,
            pims_id=self.pims_id,
            radboud_id=self.radboud_id,
        )
        logger.debug("Token obtained.")
        return {"authorization": "bearer " + token}

    def __call__(self, r):
        """Called before sending the request"""

        # Make sure keep alive because session is authenticated, not just the
        # connection
        r.headers["Connection"] = "Keep-Alive"
        if not self._bearer_token:
            self._bearer_token = (
                self.get_token()
            )  # first call, obtain new token
        r.headers.update(self._bearer_token)
        r.register_hook("response", self.response_hook)
        return r
