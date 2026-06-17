from src.auth import get_google_credentials
from src.config import Config

def test_get_google_credentials_valid(monkeypatch):
    monkeypatch.setattr(Config, "GOOGLE_OAUTH_CLIENT_ID", "test_id")
    monkeypatch.setattr(Config, "GOOGLE_OAUTH_CLIENT_SECRET", "test_secret")
    monkeypatch.setattr(Config, "GOOGLE_OAUTH_REFRESH_TOKEN", "test_refresh")
    monkeypatch.setattr(Config, "GROQ_API_KEY", "test_groq")
    monkeypatch.setattr(Config, "KNOWLEDGE_DRIVE_FOLDER_ID", "test_folder")

    creds = get_google_credentials()
    assert creds.client_id == "test_id"
    assert creds.client_secret == "test_secret"
    assert creds.refresh_token == "test_refresh"
    assert creds.token_uri == "https://oauth2.googleapis.com/token"
    assert creds.token is None
