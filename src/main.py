import base64
import argparse
from src.config import Config
from src.google_clients import get_gmail_client, get_drive_client
from src.groq_client import get_groq_client
from src.kb_sync import sync_knowledge_base, load_knowledge_base
from src.gmail_service import (
    get_owner_email,
    fetch_candidate_messages,
    is_incoming_message,
    has_human_replied,
    has_draft_reply,
    apply_labels,
    create_draft_reply
)
from src.pipeline import process_email
from src.stats import increment_stat, record_error

def extract_email_body(payload: dict) -> str:
    """Recursively extract the plain text body from the Gmail message payload."""
    if 'parts' in payload:
        for part in payload['parts']:
            if part['mimeType'] == 'text/plain':
                data = part['body'].get('data', '')
                if data:
                    return base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
            elif 'parts' in part:
                body = extract_email_body(part)
                if body:
                    return body
    else:
        if payload.get('mimeType') == 'text/plain':
            data = payload.get('body', {}).get('data', '')
            if data:
                return base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
    return ""

def run_agent(dry_run: bool = False):
    try:
        Config.validate()
        gmail_client = get_gmail_client()
        drive_client = get_drive_client()
        groq_client = get_groq_client()
        
        sync_knowledge_base(drive_client)
        kb_text = load_knowledge_base()
        
        owner_email = get_owner_email(gmail_client)
        candidate_messages = fetch_candidate_messages(gmail_client)
        
        for msg in candidate_messages:
            try:
                msg_id = msg['id']
                thread_id = msg['threadId']
                timestamp = int(msg.get('internalDate', 0))
                payload = msg.get('payload', {})
                
                if not is_incoming_message(msg, owner_email):
                    if dry_run:
                        print(f"[DRY RUN] Would skip outgoing message {msg_id} and apply {Config.LABEL_PROCESSED}")
                    else:
                        apply_labels(gmail_client, msg_id, [Config.LABEL_PROCESSED], [])
                        increment_stat("skipped")
                        increment_stat("processed")
                    continue
                    
                if has_human_replied(gmail_client, thread_id, timestamp, owner_email):
                    if dry_run:
                        print(f"[DRY RUN] Would skip thread {thread_id} (already replied) and apply {Config.LABEL_PROCESSED}")
                    else:
                        apply_labels(gmail_client, msg_id, [Config.LABEL_PROCESSED], [])
                        increment_stat("skipped")
                        increment_stat("processed")
                    continue
                    
                if has_draft_reply(gmail_client, thread_id):
                    if dry_run:
                        print(f"[DRY RUN] Would skip thread {thread_id} (draft exists) and apply {Config.LABEL_PROCESSED}")
                    else:
                        apply_labels(gmail_client, msg_id, [Config.LABEL_PROCESSED], [])
                        increment_stat("skipped")
                        increment_stat("processed")
                    continue
                    
                email_body = extract_email_body(payload)
                if not email_body:
                    email_body = msg.get('snippet', '')
                
                result = process_email(groq_client, email_body, kb_text)
                status = result['status']
                reply_body = result['reply']
                
                if status == "SKIPPED_NOT_QUERY":
                    if dry_run:
                        print(f"[DRY RUN] SKIPPED_NOT_QUERY for {msg_id}. Would apply {Config.LABEL_PROCESSED}")
                    else:
                        apply_labels(gmail_client, msg_id, [Config.LABEL_PROCESSED], [])
                        increment_stat("skipped")
                elif status == "NO_ANSWER_FOUND":
                    if dry_run:
                        print(f"[DRY RUN] NO_ANSWER_FOUND for {msg_id}. Would apply {Config.LABEL_NEEDS_HUMAN}")
                    else:
                        apply_labels(gmail_client, msg_id, [Config.LABEL_PROCESSED, Config.LABEL_NEEDS_HUMAN], [])
                        increment_stat("flagged")
                elif status == "DRAFT_GENERATED":
                    if dry_run:
                        print(f"[DRY RUN] DRAFT_GENERATED for {msg_id}. Would create draft.")
                    else:
                        create_draft_reply(gmail_client, msg, reply_body)
                        apply_labels(gmail_client, msg_id, [Config.LABEL_PROCESSED], [])
                        increment_stat("drafts")
                
                if not dry_run:
                    increment_stat("processed")
                
            except Exception as e:
                if dry_run:
                    print(f"[DRY RUN] Error processing message {msg.get('id')}: {str(e)}")
                else:
                    record_error(f"Error processing message {msg.get('id')}: {str(e)}")
                    increment_stat("errors")
                
    except Exception as e:
        if dry_run:
            print(f"[DRY RUN] Critical error in run_agent: {str(e)}")
        else:
            record_error(f"Critical error in run_agent: {str(e)}")
        raise
        
    if dry_run:
        print("[DRY RUN] Would attempt to send daily digest.")
    else:
        # Attempt to send daily digest
        try:
            from src.digest import send_digest_email
            send_digest_email(gmail_client)
        except Exception as e:
            record_error(f"Failed to send digest: {str(e)}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Email Triage Agent")
    parser.add_argument("--dry-run", action="store_true", help="Run without mutating Gmail state")
    args = parser.parse_args()
    
    run_agent(dry_run=args.dry_run)
