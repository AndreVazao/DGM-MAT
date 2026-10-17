from pathlib import Path

import pytest

from core.learning.learning_engine import LearningEngine


def test_execution_observations_persist_without_raw_error_or_prompt(tmp_path):
    path = tmp_path / "execution-observations.jsonl"
    engine = LearningEngine(path)

    record = engine.learn_from_execution({
        "mission_id": "mission_123",
        "handler": "repo_scan",
        "status": "FAILED",
        "success": False,
        "error_type": "ProviderUnavailable",
        "error": "private-token=DO_NOT_PERSIST",
        "goal": "private prompt must not be stored",
        "duration_seconds": 90000,
    })

    assert record["status"] == "FAILED"
    assert record["success"] is False
    assert record["error_type"] == "ProviderUnavailable"
    assert record["duration_seconds"] == 86400.0
    assert record["promotion_status"] == "OBSERVATION_ONLY"

    stored = path.read_text(encoding="utf-8")
    assert "DO_NOT_PERSIST" not in stored
    assert "private prompt" not in stored
    assert "private-token" not in stored

    restored = LearningEngine(path)
    assert len(restored.learnings) == 1
    assert restored.learnings[0]["observation_id"] == record["observation_id"]
    assert restored.summarize() == {
        "observations": 1,
        "successful": 0,
        "failed": 1,
        "unique_patterns": 1,
        "lesson_promotion": "requires independent validation",
    }


def test_success_observation_does_not_store_error_payload(tmp_path):
    path = tmp_path / "observations.jsonl"
    engine = LearningEngine(path)

    record = engine.learn_from_execution({
        "mission_id": "mission_success",
        "handler": "list_repositories",
        "status": "COMPLETED",
        "success": True,
        "error": "must not be stored",
        "duration_seconds": 0.25,
    })

    assert record["success"] is True
    assert record["error_type"] == "none"
    assert "must not be stored" not in path.read_text(encoding="utf-8")


def test_learning_engine_rejects_non_dictionary_execution_data(tmp_path):
    engine = LearningEngine(tmp_path / "observations.jsonl")

    with pytest.raises(TypeError, match="execution_data must be a dictionary"):
        engine.learn_from_execution("not an execution record")

    assert not engine.observations_path.exists()
