import os
import json
import time
from unittest.mock import MagicMock, patch
from src.digest import should_send_digest, generate_digest_body, send_digest_email
from src.config import Config

def test_should_send_digest(tmp_path):
    path = str(tmp_path / "last.json")
    
    # Missing file -> True
    assert should_send_digest(path) == True
    
    # Fresh file -> False
    with open(path, 'w') as f:
        json.dump({"last_sent": time.time()}, f)
    assert should_send_digest(path) == False
    
    # Old file -> True
    with open(path, 'w') as f:
        json.dump({"last_sent": time.time() - 90000}, f)
    assert should_send_digest(path) == True

def test_generate_digest_body():
    stats = {
        "processed": 5,
        "drafts": 2,
        "flagged": 1,
        "skipped": 2,
        "errors": ["Connection timeout"]
    }
    
    body = generate_digest_body(stats)
    assert "Total Emails Processed: 5" in body
    assert "Draft Replies Generated: 2" in body
    assert "Connection timeout" in body

@patch('src.digest.time.time')
@patch('src.digest.load_stats')
@patch('src.digest.save_stats')
@patch('src.digest.Config')
def test_send_digest_email(mock_config, mock_save_stats, mock_load_stats, mock_time, tmp_path):
    last_path = str(tmp_path / "last.json")
    stats_path = str(tmp_path / "stats.json")
    
    mock_config.DIGEST_RECIPIENT_EMAIL = "owner@test.com"
    mock_load_stats.return_value = {"processed": 1}
    mock_time.return_value = 1000000
    
    mock_client = MagicMock()
    
    # Should send
    assert send_digest_email(mock_client, last_path, stats_path) == True
    
    # Verify sent
    mock_client.users().messages().send.assert_called_once()
    
    # Verify last_sent updated
    with open(last_path, 'r') as f:
        data = json.load(f)
    assert data['last_sent'] == 1000000
    
    # Verify stats cleared
    mock_save_stats.assert_called_once_with({"processed": 0, "drafts": 0, "flagged": 0, "skipped": 0, "errors": []}, stats_path)

    # Calling again should not send since we just wrote the file
    mock_time.return_value = 1000010
    assert send_digest_email(mock_client, last_path, stats_path) == False
