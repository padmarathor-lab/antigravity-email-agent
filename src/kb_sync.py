import io
import os
from googleapiclient.http import MediaIoBaseDownload
from src.manifest import load_manifest, save_manifest
from src.extractors.pdf import extract_text_from_pdf
from src.extractors.docx import extract_text_from_docx
from src.config import Config

def list_drive_files(drive_client, folder_id: str) -> list[dict]:
    query = f"'{folder_id}' in parents and trashed = false"
    results = drive_client.files().list(
        q=query,
        fields="files(id, name, modifiedTime, mimeType)",
        pageSize=1000
    ).execute()
    
    return results.get('files', [])

def download_drive_file(drive_client, file_id: str) -> io.BytesIO:
    request = drive_client.files().get_media(fileId=file_id)
    file_stream = io.BytesIO()
    downloader = MediaIoBaseDownload(file_stream, request)
    done = False
    while done is False:
        status, done = downloader.next_chunk()
    file_stream.seek(0)
    return file_stream

def sync_knowledge_base(drive_client):
    Config.validate()
    folder_id = Config.KNOWLEDGE_DRIVE_FOLDER_ID
    
    drive_files = list_drive_files(drive_client, folder_id)
    manifest = load_manifest()
    manifest_files = manifest.get("files", {})
    
    current_drive_ids = set()
    
    os.makedirs("knowledge/extracted", exist_ok=True)
    
    for df in drive_files:
        file_id = df['id']
        name = df['name']
        modified_time = df['modifiedTime']
        mime_type = df.get('mimeType', '')
        
        current_drive_ids.add(file_id)
        
        needs_update = False
        if file_id not in manifest_files:
            needs_update = True
        elif manifest_files[file_id]['modifiedTime'] != modified_time:
            needs_update = True
            
        if needs_update:
            try:
                file_stream = download_drive_file(drive_client, file_id)
                extracted_text = ""
                
                if "pdf" in mime_type or name.lower().endswith(".pdf"):
                    extracted_text = extract_text_from_pdf(file_stream)
                elif "document" in mime_type or name.lower().endswith(".docx"):
                    extracted_text = extract_text_from_docx(file_stream)
                else:
                    continue
                
                out_path = f"knowledge/extracted/{file_id}.txt"
                with open(out_path, 'w', encoding='utf-8') as f:
                    f.write(extracted_text)
                    
                manifest_files[file_id] = {
                    "name": name,
                    "modifiedTime": modified_time
                }
            except Exception as e:
                print(f"Error processing file {name} ({file_id}): {e}")
                
    removed_ids = set(manifest_files.keys()) - current_drive_ids
    for rm_id in list(removed_ids):
        out_path = f"knowledge/extracted/{rm_id}.txt"
        if os.path.exists(out_path):
            os.remove(out_path)
        del manifest_files[rm_id]
        
    manifest["files"] = manifest_files
    save_manifest(manifest)

def load_knowledge_base() -> str:
    extracted_dir = "knowledge/extracted"
    if not os.path.exists(extracted_dir):
        return ""
        
    manifest = load_manifest()
    manifest_files = manifest.get("files", {})
    
    combined = []
    
    for filename in os.listdir(extracted_dir):
        if filename.endswith(".txt"):
            file_id = filename.replace(".txt", "")
            original_name = manifest_files.get(file_id, {}).get("name", "Unknown Document")
            
            filepath = os.path.join(extracted_dir, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                
            combined.append(f"--- Document: {original_name} ---\n{content}")
            
    return "\n\n".join(combined)
