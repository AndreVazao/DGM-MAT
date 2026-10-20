import pytest

from core.autonomy.mission_engine import MissionEngine
from core.autonomy.mission_models import Mission, MissionStatus


@pytest.mark.parametrize(
    "terminal_status",
    [MissionStatus.COMPLETED, MissionStatus.CANCELLED, MissionStatus.FAILED],
)
@pytest.mark.parametrize("finalizer", ["success", "failure"])
def test_finalizer_refuses_stale_cache_when_checkpoint_is_terminal(
    tmp_path, monkeypatch, terminal_status, finalizer
):
    engine = MissionEngine()
    engine.missions_path = tmp_path
    monkeypatch.setattr(engine, "_sync_state", lambda mission: None)
    emitted = []
    observed = []
    monkeypatch.setattr(engine, "_emit_mission_result", lambda mission, result: emitted.append(result))
    monkeypatch.setattr(
        engine,
        "_record_execution_observation",
        lambda mission, result, status: observed.append((result, status)),
    )

    mission_id = f"terminal-finalizer-{terminal_status.value.lower()}-{finalizer}"
    existing_result = {"status": terminal_status.value.lower(), "output": "persisted terminal result"}
    durable = Mission(
        mission_id=mission_id,
        goal="Preserve terminal result",
        description="Regression: stale worker must not overwrite a terminal checkpoint",
        status=terminal_status,
        metadata={"result": existing_result, "output": existing_result["output"]},
    )
    engine.active_missions[mission_id] = durable
    engine.save_mission(durable)

    # A worker in another process still holds an old RUNNING object.
    stale = Mission(
        mission_id=mission_id,
        goal=durable.goal,
        description=durable.description,
        status=MissionStatus.RUNNING,
        metadata={"stale_cache": True},
    )
    engine.active_missions[mission_id] = stale

    if finalizer == "success":
        result = engine._finish_mission_success(
            stale,
            {"status": "completed", "mission_id": mission_id, "output": "late stale result"},
        )
    else:
        result = engine._finish_mission_failure(
            stale, RuntimeError("late stale failure")
        )

    assert result is None
    assert stale.status is terminal_status
    assert stale.metadata["result"] == existing_result
    assert stale.metadata["output"] == existing_result["output"]
    assert "stale_cache" not in stale.metadata
    assert emitted == []
    assert observed == []

    import json
    persisted = json.loads((tmp_path / f"{mission_id}.json").read_text(encoding="utf-8"))
    assert persisted["status"] == terminal_status.value
    assert persisted["metadata"]["result"] == existing_result
