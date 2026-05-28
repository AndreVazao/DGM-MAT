import pytest
from core.runtime.health_score import RuntimeHealthScore

def test_health_score_perfect():
    engine = RuntimeHealthScore()
    summary = {
        "is_runtime_healthy": True,
        "active_providers": 1,
        "total_repos": 1
    }

    result = engine.compute(summary)
    assert result["score"] == 100
    assert len(result["warnings"]) == 0
    assert len(result["critical"]) == 0

def test_health_score_degraded():
    engine = RuntimeHealthScore()
    summary = {
        "is_runtime_healthy": False,
        "active_providers": 0,
        "total_repos": 0
    }

    result = engine.compute(summary)
    assert result["score"] < 100
    assert len(result["critical"]) > 0
