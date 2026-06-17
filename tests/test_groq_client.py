from unittest.mock import patch
from src.groq_client import get_groq_client
from src.config import Config

@patch('src.groq_client.Groq')
def test_get_groq_client(mock_groq, monkeypatch):
    monkeypatch.setattr(Config, "GOOGLE_OAUTH_CLIENT_ID", "test_id")
    monkeypatch.setattr(Config, "GOOGLE_OAUTH_CLIENT_SECRET", "test_secret")
    monkeypatch.setattr(Config, "GOOGLE_OAUTH_REFRESH_TOKEN", "test_refresh")
    monkeypatch.setattr(Config, "KNOWLEDGE_DRIVE_FOLDER_ID", "test_folder")
    monkeypatch.setattr(Config, "GROQ_API_KEY", "test_groq_key")
    
    client = get_groq_client()
    
    mock_groq.assert_called_once_with(api_key="test_groq_key")
    assert client == mock_groq.return_value
