import pytest
from core.runtime.health_score import RuntimeHealthScore

def test_health_breakdown_nominal():
    engine = RuntimeHealthScore()
    summary = {
        "is_runtime_healthy": True,
        "canonical_paths_valid": True,
        "active_providers": 1,
        "total_repos": 1,
        "queue_health": {"worker_alive": True}
    }
    result = engine.compute(summary)
    assert result["status"] == "NOMINAL"
    assert result["score"] >= 90
    assert "bootstrap" in result["breakdown"]
    assert result["breakdown"]["bootstrap"] == "25/25"

def test_health_breakdown_critical_missing_folders():
    engine = RuntimeHealthScore()
    summary = {
        "is_runtime_healthy": False, # Critical
        "canonical_paths_valid": True,
        "active_providers": 1,
        "total_repos": 1,
        "queue_health": {"worker_alive": True}
    }
    result = engine.compute(summary)
    assert result["status"] == "CRITICAL"
    assert result["score"] <= 49
    assert "RUNTIME_FOLDERS_MISSING" in result["degradation_reasons"]
    assert result["breakdown"]["bootstrap"] == "0/25"

def test_health_breakdown_queue_down():
    engine = RuntimeHealthScore()
    summary = {
        "is_runtime_healthy": True,
        "canonical_paths_valid": True,
        "active_providers": 1,
        "total_repos": 1,
        "queue_health": {"worker_alive": False} # Penalty
    }
    result = engine.compute(summary)
    assert result["status"] == "CRITICAL"
    assert result["score"] <= 49
    assert "QUEUE_CONSUMER_DOWN" in result["degradation_reasons"]
