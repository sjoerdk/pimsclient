from os import environ

import requests
from requests_ntlm import HttpNtlmAuth

from pimsclient.auth.exceptions import AuthError


def get_ntlm_authenticated_session(user=None, password=None):
    """Create a session with NTLM credentials attached

    Parameters
    ----------
    user: str, optional
        username to connect to PIMS API use, defaults to reading
        environment key ['PIMS_CLIENT_USER']
    password: str, optional
        password to connect to PIMS API, defaults to reading
        environment key ['PIMS_CLIENT_PASSWORD']

    Raises
    ------
    PIMSServerError
        When no username or password is given or found in env

    Returns
    -------
    Session
        Logged in requests.session object
    """
    if not user:
        user = environ.get("PIMS_CLIENT_USER")
    if not password:
        password = environ.get("PIMS_CLIENT_PASSWORD")
    if user is None or password is None:
        raise AuthError("Username and password not found. These are required")
    session = requests.Session()
    session.auth = HttpNtlmAuth(f"umcn\\{user}", password)
    return session
