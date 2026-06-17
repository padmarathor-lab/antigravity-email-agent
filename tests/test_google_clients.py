from unittest.mock import patch, MagicMock
from src.google_clients import get_gmail_client, get_drive_client

@patch('src.google_clients.build')
@patch('src.google_clients.get_google_credentials')
def test_get_gmail_client(mock_get_creds, mock_build):
    mock_creds = MagicMock()
    mock_get_creds.return_value = mock_creds
    
    client = get_gmail_client()
    
    mock_get_creds.assert_called_once()
    mock_build.assert_called_once_with('gmail', 'v1', credentials=mock_creds)
    assert client == mock_build.return_value

@patch('src.google_clients.build')
@patch('src.google_clients.get_google_credentials')
def test_get_drive_client(mock_get_creds, mock_build):
    mock_creds = MagicMock()
    mock_get_creds.return_value = mock_creds
    
    client = get_drive_client()
    
    mock_get_creds.assert_called_once()
    mock_build.assert_called_once_with('drive', 'v3', credentials=mock_creds)
    assert client == mock_build.return_value
