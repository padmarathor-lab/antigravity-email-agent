import os
from src.stats import load_stats, save_stats, increment_stat, record_error

def test_stats_operations(tmp_path):
    stats_path = str(tmp_path / "stats.json")
    
    # Load defaults
    stats = load_stats(stats_path)
    assert stats["processed"] == 0
    
    # Increment
    increment_stat("processed", stats_path)
    increment_stat("drafts", stats_path)
    increment_stat("processed", stats_path)
    
    stats = load_stats(stats_path)
    assert stats["processed"] == 2
    assert stats["drafts"] == 1
    
    # Record error
    record_error("Test Error 1", stats_path)
    record_error("Test Error 2", stats_path)
    
    stats = load_stats(stats_path)
    assert len(stats["errors"]) == 2
    assert stats["errors"][0] == "Test Error 1"
