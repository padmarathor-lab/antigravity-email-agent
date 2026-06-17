from src.config import Config
from src.groq_client import call_groq_with_retry
from src.prompts import STAGE_1_TRIAGE_PROMPT, STAGE_2_DRAFT_PROMPT

def process_email(groq_client, message_text: str, kb_text: str) -> dict:
    """
    Orchestrates the two-stage Groq pipeline.
    Returns a dictionary with 'status' and 'reply'.
    Statuses: SKIPPED_NOT_QUERY, NO_ANSWER_FOUND, DRAFT_GENERATED
    """
    
    # Stage 1: Triage
    triage_messages = [
        {"role": "system", "content": STAGE_1_TRIAGE_PROMPT},
        {"role": "user", "content": message_text}
    ]
    
    triage_result = call_groq_with_retry(
        client=groq_client,
        model=Config.MODEL_TRIAGE,
        messages=triage_messages
    )
    
    if "NOT_QUERY" in triage_result.upper():
        return {"status": "SKIPPED_NOT_QUERY", "reply": ""}
        
    # Stage 2: Draft
    draft_system_prompt = STAGE_2_DRAFT_PROMPT.format(kb_text=kb_text)
    draft_messages = [
        {"role": "system", "content": draft_system_prompt},
        {"role": "user", "content": message_text}
    ]
    
    draft_result = call_groq_with_retry(
        client=groq_client,
        model=Config.MODEL_DRAFT,
        messages=draft_messages
    )
    
    if "[UNANSWERED]" in draft_result.upper():
        return {"status": "NO_ANSWER_FOUND", "reply": ""}
        
    return {"status": "DRAFT_GENERATED", "reply": draft_result}
