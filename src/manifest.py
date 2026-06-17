import json
import os

def load_manifest(manifest_path: str = "knowledge/manifest.json") -> dict:
    if not os.path.exists(manifest_path):
        return {"files": {}}
    
    with open(manifest_path, 'r', encoding='utf-8') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {"files": {}}

def save_manifest(manifest_data: dict, manifest_path: str = "knowledge/manifest.json") -> None:
    os.makedirs(os.path.dirname(manifest_path), exist_ok=True)
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest_data, f, indent=2)
