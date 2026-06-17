import base64
from email.message import EmailMessage
from src.config import Config

_OWNER_EMAIL_CACHE = None

def get_owner_email(gmail_client) -> str:
    global _OWNER_EMAIL_CACHE
    if not _OWNER_EMAIL_CACHE:
        profile = gmail_client.users().getProfile(userId='me').execute()
        _OWNER_EMAIL_CACHE = profile.get('emailAddress', '')
    return _OWNER_EMAIL_CACHE

def fetch_candidate_messages(gmail_client) -> list[dict]:
    Config.validate()
    query = f"-label:{Config.LABEL_PROCESSED} label:INBOX"
    results = gmail_client.users().messages().list(userId='me', q=query).execute()
    messages = results.get('messages', [])
    
    detailed_messages = []
    for msg in messages:
        msg_detail = gmail_client.users().messages().get(userId='me', id=msg['id'], format='full').execute()
        detailed_messages.append(msg_detail)
        
    return detailed_messages

def get_header(message: dict, header_name: str) -> str:
    headers = message.get('payload', {}).get('headers', [])
    for header in headers:
        if header['name'].lower() == header_name.lower():
            return header['value']
    return ""

def is_incoming_message(message: dict, owner_email: str) -> bool:
    from_header = get_header(message, 'From')
    return owner_email.lower() not in from_header.lower()

def has_human_replied(gmail_client, thread_id: str, candidate_timestamp: int, owner_email: str) -> bool:
    thread = gmail_client.users().threads().get(userId='me', id=thread_id).execute()
    messages = thread.get('messages', [])
    
    for msg in messages:
        msg_time = int(msg.get('internalDate', 0))
        if msg_time > candidate_timestamp:
            if not is_incoming_message(msg, owner_email):
                return True
    return False

def has_draft_reply(gmail_client, thread_id: str) -> bool:
    results = gmail_client.users().drafts().list(userId='me').execute()
    drafts = results.get('drafts', [])
    for draft in drafts:
        # Avoid full API call if threadId is returned in list, although the API sometimes omits it
        if draft.get('message', {}).get('threadId') == thread_id:
            return True
            
        draft_detail = gmail_client.users().drafts().get(userId='me', id=draft['id']).execute()
        if draft_detail.get('message', {}).get('threadId') == thread_id:
            return True
    return False

def get_or_create_label(gmail_client, label_name: str) -> str:
    results = gmail_client.users().labels().list(userId='me').execute()
    labels = results.get('labels', [])
    for label in labels:
        if label['name'].lower() == label_name.lower():
            return label['id']
            
    new_label = {
        'name': label_name,
        'labelListVisibility': 'labelShow',
        'messageListVisibility': 'show'
    }
    created_label = gmail_client.users().labels().create(userId='me', body=new_label).execute()
    return created_label['id']

def apply_labels(gmail_client, message_id: str, add_labels: list[str], remove_labels: list[str]) -> None:
    add_label_ids = [get_or_create_label(gmail_client, name) for name in add_labels]
    remove_label_ids = [get_or_create_label(gmail_client, name) for name in remove_labels]
    
    body = {}
    if add_label_ids:
        body['addLabelIds'] = add_label_ids
    if remove_label_ids:
        body['removeLabelIds'] = remove_label_ids
        
    gmail_client.users().messages().modify(userId='me', id=message_id, body=body).execute()

def create_draft_reply(gmail_client, parent_message: dict, reply_body: str) -> dict:
    thread_id = parent_message.get('threadId', '')
    parent_id = get_header(parent_message, 'Message-ID')
    subject = get_header(parent_message, 'Subject')
    
    if not subject.lower().startswith("re:"):
        subject = f"Re: {subject}"
        
    reply_to = get_header(parent_message, 'Reply-To')
    to_address = reply_to if reply_to else get_header(parent_message, 'From')
    
    references = get_header(parent_message, 'References')
    if references:
        references = f"{references} {parent_id}"
    elif parent_id:
        references = parent_id

    message = EmailMessage()
    message.set_content(reply_body)
    message['To'] = to_address
    message['Subject'] = subject
    if parent_id:
        message['In-Reply-To'] = parent_id
    if references:
        message['References'] = references
    
    encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
    
    draft_body = {
        'message': {
            'raw': encoded_message,
            'threadId': thread_id
        }
    }
    
    return gmail_client.users().drafts().create(userId='me', body=draft_body).execute()
