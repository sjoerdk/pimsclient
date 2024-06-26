from io import StringIO
from pathlib import Path
from unittest.mock import Mock

from requests import Session
from requests_mock import ANY

from pimsclient.auth.msal import MSALAuth


A_PUBLIC_CERT = """-----BEGIN CERTIFICATE-----
MIIEdTCCA12gAwIBAgIUbpGEIh/W1oi4bIp4N2r7/gMBRE0wDQYJKoZIhvcNAQEL
BQAwgckxCzAJBgNVBAYTAk5MMRMwEQYDVQQIDApHZWxkZXJsYW5kMREwDwYDVQQH
DAhOaWptZWdlbjETMBEGA1UECgwKUmFkYm91ZHVtYzE4MDYGA1UECwwvRGVwYXJ0
bWVudCBvZiBNZWRpY2FsIEltYWdpbmcgLSBSZXNlYXJjaCBCdXJlYXUxGDAWBgNV
BAMMD1Jlc2VhcmNoIEJ1cmVhdTEpMCcGCSqGSIb3DQEJARYady5zLmtlcmtzdHJh
QHJhZGJvdWR1bWMubmwwHhcNMjMxMjA1MTA0MTIzWhcNMjQxMjA0MTA0MTIzWjCB
yTELMAkGA1UEBhMCTkwxEzARBgNVBAgMCkdlbGRlcmxhbmQxETAPBgNVBAcMCE5p
am1lZ2VuMRMwEQYDVQQKDApSYWRib3VkdW1jMTgwNgYDVQQLDC9EZXBhcnRtZW50
IG9mIE1lZGljYWwgSW1hZ2luZyAtIFJlc2VhcmNoIEJ1cmVhdTEYMBYGA1UEAwwP
UmVzZWFyY2ggQnVyZWF1MSkwJwYJKoZIhvcNAQkBFhp3LnMua2Vya3N0cmFAcmFk
Ym91ZHVtYy5ubDCCASIwDQYJKoZIhvcNAQEBBQADggEPADCCAQoCggEBALR5kF6F
Hrox9OezDiEuxU0xSYsLNn4FjdUO6iF0+jRZqz71UwPZHmGuIgr5jegnkSc4Ds+i
mLc+rQt4Lp5IIv9eYMgaIMpQqjIRSZc43Hwgx64B/rvZ5X1m4fdBvnd/XeRpe1ji
Hxai3jv4LUhEio7Fe6veCSgU5kGeX5JcwwOQTLfX1Il8vVn5yS4/xTRSvHHXhtct
wY8v/H1fH2tfgNSz3syFpkgVLZXAlDmG7nM+t3cucEWUl6GcZ/agsDmFwsPeAB2h
ZL+lkJrZ8GqyjsWsORMLLKj9bs6SNJIAFxotCjXPQdHlSvcZV5vwx+Ts1FZPZhu0
+vI9F4yiNd33dvUCAwEAAaNTMFEwHQYDVR0OBBYEFNCrdX+W3F2oN2aN6XgPXB1D
GtPSMB8GA1UdIwQYMBaAFNCrdX+W3F2oN2aN6XgPXB1DGtPSMA8GA1UdEwEB/wQF
MAMBAf8wDQYJKoZIhvcNAQELBQADggEBAFiiruNNOaTJHeI1gzUw/OKKofHInnWi
J9utAZhXAZm8RSpaCog5yZ2b85ZQxI0gpPWELG2tKNcw17WM3JQNTDu/M59g7nXQ
Bc3Yi/yROiJeuSS9PI5fxbCT9nJuZmlCIhIlIXaQsrDAZuM6UTxUcCZvsviZbKzk
Z9ysLpEnyxR96IIi/jzWVbkyvoHhOx4MLldWxuKGkNnms8AGCOQnFDVhTP/2B8IF
MuSGHxh9Rff/EZ1Q0Rq855bxkh/Lv+fOSLfHwil0rj4yXpZoiTWOp/DtBmH6CAhs
i4VWlT9in4RUSpTppCpVrnYfAZt08kmTOAB16Af0ccaldsrAwpFYOAc=
-----END CERTIFICATE-----"""


def test_re_login(requests_mock, monkeypatch):
    """Make sure automatically tries login again when token runs out"""
    # Make msal login work
    requests_mock.register_uri(ANY, ANY, text="logged in great!")
    monkeypatch.setattr("builtins.open", lambda x: StringIO("some_priv_thing"))

    # create an auth
    auth = MSALAuth(
        requester_id="mock_requester_id",
        requester_public_key=A_PUBLIC_CERT,
        requester_private_key_file=Path("any file.. mocked above"),
        pims_id="mock_pims_id",
        radboud_id="mock_radboud_id",
    )
    # which can get a token without talking to any real Microsoft server
    auth.get_token = Mock(
        spec=MSALAuth.get_token,
        return_value={"authorization": "bearer " + "OK_TOKEN"},
    )
    # Auth will start out with a token which is not accepted
    auth._bearer_token = {"authorization": "bearer " + "BAD_TOKEN"}
    session = Session()
    session.auth = auth

    # Make sure any all to any address will respond based on the authorization
    # Header. OK_TOKEN will succeed, anything else will respond with 401
    login_responses = []

    def login_response(request, context):
        login_responses.append(request)
        if request.headers.get("authorization") == "bearer OK_TOKEN":
            context.status_code = 200
            return "FINE"
        else:
            context.status_code = 401
            return "Not with that token you don't"

    requests_mock.register_uri(ANY, ANY, text=login_response)

    # no token obtaining call should have been done
    assert auth.get_token.call_count == 0
    # do call. Should have auto-obtained token now
    response = session.get("http://a_request")
    assert response.status_code == 200
    assert auth.get_token.call_count == 1
    assert (
        len(requests_mock.request_history) == 2
    )  # first request failed with 401
    assert len(login_responses) == 2  # login was called twice
