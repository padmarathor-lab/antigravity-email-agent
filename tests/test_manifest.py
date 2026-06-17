import os
import json
from src.manifest import load_manifest, save_manifest

def test_load_and_save_manifest(tmp_path):
    manifest_path = str(tmp_path / "manifest.json")
    
    # Load non-existent should return empty
    empty_manifest = load_manifest(manifest_path)
    assert empty_manifest == {"files": {}}
    
    # Save a mock manifest
    mock_data = {
        "files": {
            "123": {"name": "test.pdf", "modifiedTime": "2026-06-13T12:00:00Z"}
        }
    }
    save_manifest(mock_data, manifest_path)
    
    assert os.path.exists(manifest_path)
    
    # Load should return the saved data
    loaded = load_manifest(manifest_path)
    assert loaded == mock_data
