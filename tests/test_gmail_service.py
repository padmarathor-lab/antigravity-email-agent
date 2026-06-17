from unittest.mock import MagicMock, patch
from src.gmail_service import (
    get_owner_email,
    fetch_candidate_messages,
    get_header,
    is_incoming_message,
    has_human_replied,
    has_draft_reply,
    apply_labels,
    create_draft_reply
)
from src.config import Config

def test_get_owner_email():
    mock_client = MagicMock()
    mock_client.users().getProfile().execute.return_value = {'emailAddress': 'test@example.com'}
    
    # Needs to clear cache
    import src.gmail_service
    src.gmail_service._OWNER_EMAIL_CACHE = None
    
    email = get_owner_email(mock_client)
    assert email == 'test@example.com'

def test_fetch_candidate_messages(monkeypatch):
    monkeypatch.setattr(Config, "LABEL_PROCESSED", "Processed")
    monkeypatch.setattr(Config, "GOOGLE_OAUTH_CLIENT_ID", "id")
    monkeypatch.setattr(Config, "GOOGLE_OAUTH_CLIENT_SECRET", "sec")
    monkeypatch.setattr(Config, "GOOGLE_OAUTH_REFRESH_TOKEN", "tok")
    monkeypatch.setattr(Config, "GROQ_API_KEY", "key")
    monkeypatch.setattr(Config, "KNOWLEDGE_DRIVE_FOLDER_ID", "folder")

    mock_client = MagicMock()
    mock_messages = MagicMock()
    mock_client.users().messages.return_value = mock_messages
    
    # Mock list
    mock_list_exec = MagicMock()
    mock_list_exec.execute.return_value = {'messages': [{'id': '1'}, {'id': '2'}]}
    mock_messages.list.return_value = mock_list_exec
    
    # Mock get
    mock_get_exec1 = MagicMock()
    mock_get_exec1.execute.return_value = {'id': '1', 'snippet': 'Hello'}
    mock_get_exec2 = MagicMock()
    mock_get_exec2.execute.return_value = {'id': '2', 'snippet': 'World'}
    
    mock_messages.get.side_effect = [mock_get_exec1, mock_get_exec2]
    
    result = fetch_candidate_messages(mock_client)
    
    assert len(result) == 2
    assert result[0]['id'] == '1'
    assert result[1]['id'] == '2'

def test_get_header():
    message = {
        'payload': {
            'headers': [
                {'name': 'From', 'value': 'sender@test.com'},
                {'name': 'Subject', 'value': 'Test Subject'}
            ]
        }
    }
    assert get_header(message, 'From') == 'sender@test.com'
    assert get_header(message, 'Subject') == 'Test Subject'
    assert get_header(message, 'To') == ''

def test_is_incoming_message():
    message = {
        'payload': {
            'headers': [
                {'name': 'From', 'value': 'Owner <owner@test.com>'}
            ]
        }
    }
    assert is_incoming_message(message, 'owner@test.com') == False
    assert is_incoming_message(message, 'other@test.com') == True

def test_has_human_replied():
    mock_client = MagicMock()
    
    thread_data = {
        'messages': [
            {
                'internalDate': '100',
                'payload': {'headers': [{'name': 'From', 'value': 'customer@test.com'}]}
            },
            {
                'internalDate': '200',
                'payload': {'headers': [{'name': 'From', 'value': 'owner@test.com'}]}
            }
        ]
    }
    
    mock_client.users().threads().get().execute.return_value = thread_data
    
    # Check at time 50 (before owner reply)
    assert has_human_replied(mock_client, 'thread1', 50, 'owner@test.com') == True
    
    # Check at time 150 (after customer, before owner)
    assert has_human_replied(mock_client, 'thread1', 150, 'owner@test.com') == True
    
    # Check at time 250 (after owner reply)
    assert has_human_replied(mock_client, 'thread1', 250, 'owner@test.com') == False

def test_has_draft_reply():
    mock_client = MagicMock()
    
    mock_client.users().drafts().list().execute.return_value = {
        'drafts': [{'id': 'd1'}]
    }
    mock_client.users().drafts().get().execute.return_value = {
        'message': {'threadId': 't1'}
    }
    
    assert has_draft_reply(mock_client, 't1') == True
    assert has_draft_reply(mock_client, 't2') == False

def test_apply_labels():
    mock_client = MagicMock()
    
    mock_client.users().labels().list().execute.return_value = {
        'labels': [{'name': 'L1', 'id': 'id1'}, {'name': 'L2', 'id': 'id2'}]
    }
    
    mock_client.users().labels().create().execute.return_value = {'id': 'id3'}
    
    apply_labels(mock_client, 'msg1', add_labels=['L1', 'L3'], remove_labels=['L2'])
    
    mock_modify = mock_client.users().messages().modify
    mock_modify.assert_called_once()
    
    call_kwargs = mock_modify.call_args[1]
    assert call_kwargs['id'] == 'msg1'
    assert set(call_kwargs['body']['addLabelIds']) == {'id1', 'id3'}
    assert set(call_kwargs['body']['removeLabelIds']) == {'id2'}

def test_create_draft_reply():
    mock_client = MagicMock()
    
    parent_msg = {
        'threadId': 't1',
        'payload': {
            'headers': [
                {'name': 'Message-ID', 'value': '<msg1@test.com>'},
                {'name': 'Subject', 'value': 'Hello'},
                {'name': 'From', 'value': 'customer@test.com'},
            ]
        }
    }
    
    mock_client.users().drafts().create().execute.return_value = {'id': 'd1'}
    
    result = create_draft_reply(mock_client, parent_msg, "This is a reply.")
    
    assert result['id'] == 'd1'
    
    mock_create = mock_client.users().drafts().create
    call_kwargs = mock_create.call_args[1]
    
    draft_body = call_kwargs['body']
    assert draft_body['message']['threadId'] == 't1'
    assert 'raw' in draft_body['message']
