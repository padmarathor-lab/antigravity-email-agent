import json
import os

def load_stats(path: str = "knowledge/daily_stats.json") -> dict:
    if not os.path.exists(path):
        return {"processed": 0, "drafts": 0, "flagged": 0, "skipped": 0, "errors": []}
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {"processed": 0, "drafts": 0, "flagged": 0, "skipped": 0, "errors": []}

def save_stats(stats: dict, path: str = "knowledge/daily_stats.json") -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2)

def increment_stat(key: str, path: str = "knowledge/daily_stats.json") -> None:
    stats = load_stats(path)
    if key in stats and isinstance(stats[key], int):
        stats[key] += 1
    else:
        stats[key] = 1
    save_stats(stats, path)

def record_error(error_msg: str, path: str = "knowledge/daily_stats.json") -> None:
    stats = load_stats(path)
    if "errors" not in stats or not isinstance(stats["errors"], list):
        stats["errors"] = []
    stats["errors"].append(error_msg)
    save_stats(stats, path)
