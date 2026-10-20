import pytest

from core.autonomy.mission_engine import MissionEngine
from core.autonomy.mission_models import Mission, MissionStatus, SubTask


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



def _completed_subtask():
    return SubTask(
        subtask_id="st_completed",
        title="Work item",
        description="A task whose status alone is not mission-level result evidence",
        status="completed",
    )


def test_all_completed_subtask_flags_do_not_claim_mission_success(tmp_path, monkeypatch):
    engine = MissionEngine()
    engine.missions_path = tmp_path
    monkeypatch.setattr(engine, "_sync_state", lambda mission: None)
    failures = []
    monkeypatch.setattr(
        engine,
        "_finish_mission_failure",
        lambda mission, exc: failures.append((mission, exc)),
    )
    mission = Mission(
        mission_id="subtasks-without-result",
        goal="Complete a generic mission",
        description="Regression: completed flags are not a verified aggregate result",
        status=MissionStatus.RUNNING,
        subtasks=[_completed_subtask()],
    )
    engine.active_missions[mission.mission_id] = mission
    engine.save_mission(mission)

    engine._handle_running(mission)

    assert len(failures) == 1
    assert isinstance(failures[0][1], NotImplementedError)
    assert "no verified mission-level result" in str(failures[0][1])
    assert mission.status is MissionStatus.RUNNING
    import json
    persisted = json.loads((tmp_path / f"{mission.mission_id}.json").read_text(encoding="utf-8"))
    assert persisted["status"] == MissionStatus.RUNNING.value
    assert "result" not in persisted["metadata"]


def test_stale_completed_subtasks_cannot_overwrite_terminal_mission(tmp_path, monkeypatch):
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
    mission_id = "stale-subtasks-terminal"
    existing_result = {"status": "completed", "output": "verified prior result"}
    durable = Mission(
        mission_id=mission_id,
        goal="Preserve a terminal mission",
        description="Regression: stale completed flags cannot rewrite terminal state",
        status=MissionStatus.COMPLETED,
        metadata={"result": existing_result, "output": existing_result["output"]},
        subtasks=[_completed_subtask()],
    )
    engine.active_missions[mission_id] = durable
    engine.save_mission(durable)

    stale = Mission(
        mission_id=mission_id,
        goal=durable.goal,
        description=durable.description,
        status=MissionStatus.RUNNING,
        subtasks=[_completed_subtask()],
    )
    engine.active_missions[mission_id] = stale
    engine._handle_running(stale)

    assert stale.status is MissionStatus.COMPLETED
    assert stale.metadata["result"] == existing_result
    assert emitted == []
    assert observed == []
    import json
    persisted = json.loads((tmp_path / f"{mission_id}.json").read_text(encoding="utf-8"))
    assert persisted["status"] == MissionStatus.COMPLETED.value
    assert persisted["metadata"]["result"] == existing_result



def test_success_finalizer_returns_result_only_after_persisting_terminal_state(tmp_path, monkeypatch):
    engine = MissionEngine()
    engine.missions_path = tmp_path
    monkeypatch.setattr(engine, "_sync_state", lambda mission: None)
    monkeypatch.setattr(engine, "_emit_mission_result", lambda mission, result: None)
    monkeypatch.setattr(engine, "_record_execution_observation", lambda mission, result, status: None)
    mission = Mission(
        mission_id="success-finalizer-result-contract",
        goal="List repositories",
        description="Successful finalization must return the persisted result",
        status=MissionStatus.RUNNING,
    )
    engine.active_missions[mission.mission_id] = mission
    engine.save_mission(mission)
    result = {
        "status": "completed",
        "mission_id": mission.mission_id,
        "output": "Repository listing verified",
    }

    returned = engine._finish_mission_success(mission, result)

    assert returned is result
    assert mission.status is MissionStatus.COMPLETED
    import json
    persisted = json.loads(
        (tmp_path / f"{mission.mission_id}.json").read_text(encoding="utf-8")
    )
    assert persisted["status"] == MissionStatus.COMPLETED.value
    assert persisted["metadata"]["result"] == result


def test_queue_handler_does_not_return_success_when_finalization_is_refused(
    tmp_path, monkeypatch
):
    engine = MissionEngine()
    engine.missions_path = tmp_path
    monkeypatch.setattr(engine, "_sync_state", lambda mission: None)
    monkeypatch.setattr(
        engine,
        "_execute_list_repositories_mission",
        lambda mission: {
            "status": "completed",
            "mission_id": mission.mission_id,
            "output": "simulated result for finalization-contract test",
        },
    )
    monkeypatch.setattr(engine, "_finish_mission_success", lambda mission, result: None)
    monkeypatch.setattr(engine, "_finish_mission_failure", lambda mission, exc: None)
    mission = Mission(
        mission_id="queue-finalization-refused",
        goal="List repositories",
        description="A refused finalizer must not be reported as successful queue work",
        status=MissionStatus.RUNNING,
    )
    engine.active_missions[mission.mission_id] = mission
    engine.save_mission(mission)

    with pytest.raises(RuntimeError, match="Mission finalization was refused"):
        engine._handle_queue_execution({"mission_id": mission.mission_id})
