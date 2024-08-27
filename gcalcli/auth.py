from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow


def authenticate(client_id: str, client_secret: str):
    flow = InstalledAppFlow.from_client_config(
        client_config={
            "installed": {
                "client_id": client_id,
                "client_secret": client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url":
                    "https://www.googleapis.com/oauth2/v1/certs",
                "redirect_uris": ["http://localhost"],
            }
        },
        scopes=["https://www.googleapis.com/auth/calendar"],
    )
    credentials = flow.run_local_server(open_browser=False)
    return credentials


def refresh_if_expired(credentials) -> None:
    if credentials.expired:
        credentials.refresh(Request())
