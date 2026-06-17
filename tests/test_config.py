import os
import pytest
from src.config import Config, ConfigError

def test_config_missing_vars_raises_error(monkeypatch):
    # Clear critical env variables
    monkeypatch.delenv("GOOGLE_OAUTH_CLIENT_ID", raising=False)
    monkeypatch.delenv("GOOGLE_OAUTH_CLIENT_SECRET", raising=False)
    monkeypatch.delenv("GOOGLE_OAUTH_REFRESH_TOKEN", raising=False)
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.delenv("KNOWLEDGE_DRIVE_FOLDER_ID", raising=False)
    
    # Re-initialize fields from env (since class variables are loaded at import time,
    # we simulate the loading mechanism or mock them)
    Config.GOOGLE_OAUTH_CLIENT_ID = ""
    Config.GOOGLE_OAUTH_CLIENT_SECRET = ""
    Config.GOOGLE_OAUTH_REFRESH_TOKEN = ""
    Config.GROQ_API_KEY = ""
    Config.KNOWLEDGE_DRIVE_FOLDER_ID = ""
    
    with pytest.raises(ConfigError) as exc_info:
        Config.validate()
        
    assert "GOOGLE_OAUTH_CLIENT_ID" in str(exc_info.value)
    assert "GROQ_API_KEY" in str(exc_info.value)

def test_config_valid_vars_passes(monkeypatch):
    # Set all required fields
    Config.GOOGLE_OAUTH_CLIENT_ID = "client_id"
    Config.GOOGLE_OAUTH_CLIENT_SECRET = "client_secret"
    Config.GOOGLE_OAUTH_REFRESH_TOKEN = "refresh_token"
    Config.GROQ_API_KEY = "gsk_key"
    Config.KNOWLEDGE_DRIVE_FOLDER_ID = "folder_id"
    Config.DIGEST_RECIPIENT_EMAIL = "owner@example.com"
    
    # This should pass without raising exceptions
    Config.validate()
    
    assert Config.LABEL_PROCESSED == "Agent-Processed"
    assert Config.MODEL_TRIAGE == "llama3-8b-8192"
