from googleapiclient.discovery import build
from src.auth import get_google_credentials

def get_gmail_client(credentials=None):
    """
    Initializes and returns the Gmail API client.
    """
    if credentials is None:
        credentials = get_google_credentials()
        
    return build('gmail', 'v1', credentials=credentials)

def get_drive_client(credentials=None):
    """
    Initializes and returns the Google Drive API client.
    """
    if credentials is None:
        credentials = get_google_credentials()
        
    return build('drive', 'v3', credentials=credentials)
