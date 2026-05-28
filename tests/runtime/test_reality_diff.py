import pytest
from core.runtime.reality_diff import RealityDiffEngine, DiffSeverity

def test_reality_diff_no_drift():
    engine = RealityDiffEngine()
    desired = {
        "runtime": {"runtime": {"exists": True}},
        "repos": ["repo1"],
        "providers": ["openai"],
        "memory": {"required": True}
    }
    observed = {
        "runtime": {"runtime": {"exists": True}},
        "repos": ["repo1"],
        "providers": [{"name": "openai", "status": "active"}],
        "memory": {"exists": True}
    }

    drifts = engine.diff(desired, observed)
    assert len(drifts) == 0

def test_reality_diff_with_drift():
    engine = RealityDiffEngine()
    desired = {
        "runtime": {"runtime": {"exists": True}},
        "repos": ["repo1", "repo2"],
        "providers": ["openai"]
    }
    observed = {
        "runtime": {"runtime": {"exists": False}},
        "repos": ["repo1"],
        "providers": []
    }

    drifts = engine.diff(desired, observed)
    assert len(drifts) > 0

    types = [d["type"] for d in drifts]
    assert "runtime_drift" in types
    assert "missing_repo" in types
    assert "missing_provider" in types
