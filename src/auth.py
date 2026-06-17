from google.oauth2.credentials import Credentials
from src.config import Config

def get_google_credentials() -> Credentials:
    """
    Constructs and returns Google OAuth Credentials from the configuration.
    Validates that the necessary configuration is present.
    """
    Config.validate()
    
    return Credentials(
        token=None,
        refresh_token=Config.GOOGLE_OAUTH_REFRESH_TOKEN,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=Config.GOOGLE_OAUTH_CLIENT_ID,
        client_secret=Config.GOOGLE_OAUTH_CLIENT_SECRET,
    )
