import json
import os
import time
import base64
from email.message import EmailMessage
from src.config import Config
from src.stats import load_stats, save_stats

def should_send_digest(last_sent_path="knowledge/last_digest.json") -> bool:
    if not os.path.exists(last_sent_path):
        return True
    try:
        with open(last_sent_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            last_time = data.get("last_sent", 0)
            return (time.time() - last_time) >= 86400
    except json.JSONDecodeError:
        return True

def generate_digest_body(stats: dict) -> str:
    lines = [
        "Hello!",
        "",
        "Here is the daily execution digest for your Email Agent:",
        "",
        f"- Total Emails Processed: {stats.get('processed', 0)}",
        f"- Draft Replies Generated: {stats.get('drafts', 0)}",
        f"- Emails Skipped (Not Queries / Already Handled): {stats.get('skipped', 0)}",
        f"- Emails Flagged for Human (Unanswered by KB): {stats.get('flagged', 0)}",
        f"- Errors Encountered: {len(stats.get('errors', []))}",
    ]
    
    if stats.get('errors'):
        lines.append("")
        lines.append("Error Log:")
        for err in stats['errors']:
            lines.append(f"  - {err}")
            
    lines.extend([
        "",
        "Have a great day!",
        "- Antigravity Email Agent"
    ])
    
    return "\n".join(lines)

def send_digest_email(gmail_client, last_sent_path="knowledge/last_digest.json", stats_path="knowledge/daily_stats.json") -> bool:
    if not should_send_digest(last_sent_path):
        return False
        
    Config.validate()
    if not Config.DIGEST_RECIPIENT_EMAIL:
        return False
        
    stats = load_stats(stats_path)
    body = generate_digest_body(stats)
    
    message = EmailMessage()
    message.set_content(body)
    message['To'] = Config.DIGEST_RECIPIENT_EMAIL
    message['Subject'] = "Daily Email Agent Digest"
    
    encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
    
    gmail_client.users().messages().send(
        userId='me',
        body={'raw': encoded_message}
    ).execute()
    
    os.makedirs(os.path.dirname(last_sent_path), exist_ok=True)
    with open(last_sent_path, 'w', encoding='utf-8') as f:
        json.dump({"last_sent": time.time()}, f)
        
    save_stats({"processed": 0, "drafts": 0, "flagged": 0, "skipped": 0, "errors": []}, stats_path)
    return True
