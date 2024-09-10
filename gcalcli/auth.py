from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials


def authenticate(client_id: str, client_secret: str):
    flow = InstalledAppFlow.from_client_config(
        client_config={
            "installed": {
                "client_id": client_id,
                "client_secret": client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "redirect_uris": ["http://localhost"],
            }
        },
        scopes=["https://www.googleapis.com/auth/calendar"],
    )
    try:
        credentials = flow.run_local_server(open_browser=False)
    except RecursionError:
        raise OSError(
            'Failed to fetch credentials. If this is a nonstandard gcalcli '
            'install, please try again with a system-installed gcalcli as a '
            'workaround.\n'
            'Details: https://github.com/insanum/gcalcli/issues/735.'
        )
    return credentials


def refresh_if_expired(credentials) -> None:
    if credentials.expired:
        credentials.refresh(Request())


def creds_from_legacy_json(data):
    kwargs = {
        k: v
        for k, v in data.items()
        if k
        in (
            'client_id',
            'client_secret',
            'refresh_token',
            'token_uri',
            'scopes',
        )
    }
    return Credentials(data['access_token'], **kwargs)
