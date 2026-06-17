import os
from unittest.mock import patch, MagicMock
from src.kb_sync import list_drive_files, sync_knowledge_base, load_knowledge_base
from src.config import Config

def test_list_drive_files():
    mock_client = MagicMock()
    mock_files = MagicMock()
    mock_list = MagicMock()
    
    mock_client.files.return_value = mock_files
    mock_files.list.return_value = mock_list
    mock_list.execute.return_value = {
        'files': [{'id': '1', 'name': 'test.pdf', 'modifiedTime': 'time'}]
    }
    
    files = list_drive_files(mock_client, 'folder123')
    assert len(files) == 1
    assert files[0]['id'] == '1'

@patch('src.kb_sync.load_manifest')
@patch('src.kb_sync.save_manifest')
@patch('src.kb_sync.download_drive_file')
@patch('src.kb_sync.extract_text_from_pdf')
@patch('src.kb_sync.list_drive_files')
def test_sync_knowledge_base(mock_list, mock_extract, mock_download, mock_save, mock_load, monkeypatch, tmp_path):
    monkeypatch.setattr(Config, "KNOWLEDGE_DRIVE_FOLDER_ID", "folder123")
    monkeypatch.setattr(Config, "GOOGLE_OAUTH_CLIENT_ID", "id")
    monkeypatch.setattr(Config, "GOOGLE_OAUTH_CLIENT_SECRET", "sec")
    monkeypatch.setattr(Config, "GOOGLE_OAUTH_REFRESH_TOKEN", "tok")
    monkeypatch.setattr(Config, "GROQ_API_KEY", "key")
    
    # Use a tmp extracted path
    extracted_dir = tmp_path / "knowledge" / "extracted"
    os.makedirs(extracted_dir, exist_ok=True)
    monkeypatch.chdir(tmp_path)
    
    # Mock data
    mock_list.return_value = [
        {'id': 'file1', 'name': 'doc.pdf', 'modifiedTime': 't1', 'mimeType': 'application/pdf'}
    ]
    mock_load.return_value = {"files": {}}
    mock_download.return_value = MagicMock()
    mock_extract.return_value = "Extracted PDF Text"
    
    mock_client = MagicMock()
    sync_knowledge_base(mock_client)
    
    # Assert saving manifest was called with the new file
    mock_save.assert_called_once()
    saved_data = mock_save.call_args[0][0]
    assert 'file1' in saved_data['files']
    
    # Assert file was written
    assert os.path.exists("knowledge/extracted/file1.txt")
    with open("knowledge/extracted/file1.txt", 'r') as f:
        assert f.read() == "Extracted PDF Text"
