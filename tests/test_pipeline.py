import pytest
from unittest.mock import MagicMock, patch
from src.pipeline import process_email
from src.groq_client import call_groq_with_retry

def test_call_groq_with_retry_success():
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = "SUCCESS"
    mock_response.choices = [mock_choice]
    mock_client.chat.completions.create.return_value = mock_response
    
    result = call_groq_with_retry(mock_client, "model", [])
    assert result == "SUCCESS"
    assert mock_client.chat.completions.create.call_count == 1

def test_call_groq_with_retry_failure_then_success(monkeypatch):
    import src.groq_client
    monkeypatch.setattr(src.groq_client.time, "sleep", lambda x: None)
    
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = "SUCCESS_AFTER_RETRY"
    mock_response.choices = [mock_choice]
    
    # Fail twice, then succeed
    mock_client.chat.completions.create.side_effect = [
        Exception("Error 1"),
        Exception("Error 2"),
        mock_response
    ]
    
    result = call_groq_with_retry(mock_client, "model", [])
    assert result == "SUCCESS_AFTER_RETRY"
    assert mock_client.chat.completions.create.call_count == 3

def test_call_groq_with_retry_always_fails(monkeypatch):
    import src.groq_client
    monkeypatch.setattr(src.groq_client.time, "sleep", lambda x: None)
    
    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = Exception("Permanent Error")
    
    with pytest.raises(Exception, match="Permanent Error"):
        call_groq_with_retry(mock_client, "model", [], max_retries=2)
        
    assert mock_client.chat.completions.create.call_count == 2

@patch('src.pipeline.call_groq_with_retry')
def test_process_email_not_query(mock_call):
    # Mock triage to return NOT_QUERY
    mock_call.return_value = "NOT_QUERY"
    
    mock_client = MagicMock()
    result = process_email(mock_client, "receipt text", "kb")
    
    assert result['status'] == "SKIPPED_NOT_QUERY"
    assert result['reply'] == ""
    assert mock_call.call_count == 1

@patch('src.pipeline.call_groq_with_retry')
def test_process_email_unanswered(mock_call):
    # Triage returns CUSTOMER_QUERY, draft returns [UNANSWERED]
    mock_call.side_effect = ["CUSTOMER_QUERY", "[UNANSWERED]"]
    
    mock_client = MagicMock()
    result = process_email(mock_client, "how to jump?", "kb info on flying")
    
    assert result['status'] == "NO_ANSWER_FOUND"
    assert result['reply'] == ""
    assert mock_call.call_count == 2

@patch('src.pipeline.call_groq_with_retry')
def test_process_email_draft_generated(mock_call):
    # Triage returns CUSTOMER_QUERY, draft returns generated text
    mock_call.side_effect = ["CUSTOMER_QUERY", "Here is your answer. [SIGNATURE_PLACEHOLDER — to be replaced with team's standard sign-off]"]
    
    mock_client = MagicMock()
    result = process_email(mock_client, "how to fly?", "kb info on flying")
    
    assert result['status'] == "DRAFT_GENERATED"
    assert "Here is your answer" in result['reply']
    assert mock_call.call_count == 2
