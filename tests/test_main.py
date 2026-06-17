from unittest.mock import patch, MagicMock
from src.main import run_agent, extract_email_body

def test_extract_email_body():
    payload = {
        'mimeType': 'multipart/alternative',
        'parts': [
            {
                'mimeType': 'text/plain',
                'body': {'data': 'SGVsbG8gV29ybGQ='} # "Hello World" in base64
            }
        ]
    }
    assert extract_email_body(payload) == "Hello World"

@patch('src.main.get_gmail_client')
@patch('src.main.get_drive_client')
@patch('src.main.get_groq_client')
@patch('src.main.sync_knowledge_base')
@patch('src.main.load_knowledge_base')
@patch('src.main.get_owner_email')
@patch('src.main.fetch_candidate_messages')
@patch('src.main.is_incoming_message')
@patch('src.main.has_human_replied')
@patch('src.main.has_draft_reply')
@patch('src.main.process_email')
@patch('src.main.create_draft_reply')
@patch('src.main.apply_labels')
@patch('src.main.increment_stat')
@patch('src.main.Config')
def test_run_agent(mock_config, mock_increment, mock_apply, mock_create_draft, mock_process, mock_has_draft, mock_has_human,
                   mock_is_incoming, mock_fetch, mock_owner, mock_load_kb, mock_sync, 
                   mock_groq, mock_drive, mock_gmail):
                   
    mock_gmail_client = MagicMock()
    mock_gmail.return_value = mock_gmail_client
    mock_owner.return_value = "owner@test.com"
    
    msg_draft = {'id': 'msg1', 'threadId': 't1', 'payload': {}}
    msg_flag = {'id': 'msg2', 'threadId': 't2', 'payload': {}}
    msg_skip = {'id': 'msg3', 'threadId': 't3', 'payload': {}}
    
    mock_fetch.return_value = [msg_draft, msg_flag, msg_skip]
    
    mock_is_incoming.return_value = True
    mock_has_human.return_value = False
    mock_has_draft.return_value = False
    
    mock_process.side_effect = [
        {'status': 'DRAFT_GENERATED', 'reply': 'Test Draft'},
        {'status': 'NO_ANSWER_FOUND', 'reply': ''},
        {'status': 'SKIPPED_NOT_QUERY', 'reply': ''}
    ]
    
    run_agent(dry_run=False)
    
    assert mock_process.call_count == 3
    mock_create_draft.assert_called_once_with(mock_gmail_client, msg_draft, 'Test Draft')
    assert mock_apply.call_count == 3

@patch('src.main.get_gmail_client')
@patch('src.main.get_drive_client')
@patch('src.main.get_groq_client')
@patch('src.main.sync_knowledge_base')
@patch('src.main.load_knowledge_base')
@patch('src.main.get_owner_email')
@patch('src.main.fetch_candidate_messages')
@patch('src.main.is_incoming_message')
@patch('src.main.has_human_replied')
@patch('src.main.has_draft_reply')
@patch('src.main.process_email')
@patch('src.main.create_draft_reply')
@patch('src.main.apply_labels')
@patch('src.main.increment_stat')
@patch('src.main.Config')
def test_run_agent_dry_run(mock_config, mock_increment, mock_apply, mock_create_draft, mock_process, mock_has_draft, mock_has_human,
                   mock_is_incoming, mock_fetch, mock_owner, mock_load_kb, mock_sync, 
                   mock_groq, mock_drive, mock_gmail):
                   
    mock_gmail_client = MagicMock()
    mock_gmail.return_value = mock_gmail_client
    mock_owner.return_value = "owner@test.com"
    
    msg_draft = {'id': 'msg1', 'threadId': 't1', 'payload': {}}
    mock_fetch.return_value = [msg_draft]
    mock_is_incoming.return_value = True
    mock_has_human.return_value = False
    mock_has_draft.return_value = False
    
    mock_process.return_value = {'status': 'DRAFT_GENERATED', 'reply': 'Test Draft'}
    
    run_agent(dry_run=True)
    
    # Process gets called, but no mutations
    assert mock_process.call_count == 1
    mock_create_draft.assert_not_called()
    mock_apply.assert_not_called()
    mock_increment.assert_not_called()
