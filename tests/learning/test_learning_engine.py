import pytest

from core.learning.learning_engine import LearningEngine
from core.autonomy.mission_engine import MissionEngine
from core.autonomy.mission_models import Mission, MissionStatus
from core.organization.message_bus import InternalMessageBus


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



def test_mission_engine_records_terminal_outcome_observation(tmp_path, monkeypatch):
    engine = MissionEngine(organization_bus=InternalMessageBus())
    engine.learning_engine = LearningEngine(tmp_path / "mission-observations.jsonl")
    monkeypatch.setattr(engine, "save_mission", lambda mission: None)
    monkeypatch.setattr(engine, "_sync_state", lambda mission: None)

    mission = Mission(
        mission_id="mission_learning_hook",
        goal="Verify learning hook",
        description="A test-only mission",
        status=MissionStatus.RUNNING,
    )
    result = {
        "mission_id": mission.mission_id,
        "handler": "test_executor",
        "execution_duration": 0.125,
    }

    engine._record_execution_observation(mission, result, MissionStatus.COMPLETED)

    assert mission.metadata["learning_observation"]["status"] == "RECORDED"
    assert mission.metadata["learning_observation"]["promotion_status"] == "OBSERVATION_ONLY"
    restored = LearningEngine(engine.learning_engine.observations_path)
    assert len(restored.learnings) == 1
    assert restored.learnings[0]["mission_id"] == mission.mission_id
    assert restored.learnings[0]["status"] == "COMPLETED"
    assert restored.learnings[0]["success"] is True
