# Path: C:\ProgramasGodMode\DGM-MAT\tests\unit\test_execution_director_truthfulness.py
from core.autonomy.active_runtime.autonomy_cycle import AutonomyCycle
from core.autonomy.active_runtime.execution_director import ExecutionDirector


def test_execution_director_never_claims_unexecuted_tasks_are_validated():
    director = ExecutionDirector()
    task_ids = director.assign_tasks([{"title": "repair API"}, {"title": "audit security"}])
    assert task_ids == ["planned_task_0", "planned_task_1"]
    assert director.validate_execution(task_ids) == {
        "planned_task_0": "NOT_EXECUTED",
        "planned_task_1": "NOT_EXECUTED",
    }


def test_cycle_close_preserves_failed_status():
    cycle = AutonomyCycle()
    cycle.status = "FAILED"
    cycle.complete()
    assert cycle.status == "FAILED"
    assert cycle.end_time is not None


def test_cycle_close_preserves_partial_status():
    cycle = AutonomyCycle()
    cycle.status = "PARTIAL"
    cycle.complete()
    assert cycle.status == "PARTIAL"
    assert cycle.end_time is not None


def test_cycle_close_marks_normal_cycle_completed():
    cycle = AutonomyCycle()
    cycle.complete()
    assert cycle.status == "COMPLETED"


def test_cognition_cycle_reports_planned_work_as_partial(tmp_path, monkeypatch):
    import asyncio
    import json
    from types import SimpleNamespace

    import core.autonomy.active_runtime.cognition_loop as cognition_module
    from core.autonomy.active_runtime.cognition_loop import CognitionLoop

    monkeypatch.setattr(cognition_module, "safe_broadcast", lambda payload: None)
    monkeypatch.setattr(
        cognition_module,
        "mission_engine",
        SimpleNamespace(process_missions=lambda: None),
    )
    loop = CognitionLoop()
    loop.storage_path = tmp_path
    loop.repo_scanner = SimpleNamespace(scan=lambda: {"sample.py": {}})
    loop.planner = SimpleNamespace(analyze_repository=lambda: {"detected_gaps": ["sample defect"]})
    loop.objective_engine = SimpleNamespace(
        generate_objectives=lambda analysis: [
            {"title": "repair sample", "priority": 70, "approval_required": True}
        ]
    )
    loop.learning_loop = SimpleNamespace(
        reflect_on_cycle=lambda cycle: {"observed": True},
        store_experience=lambda cycle: None,
        generate_self_improvements=lambda reflection: [],
    )

    asyncio.run(loop.run_cycle())
    cycle_file = next(tmp_path.glob("cycle_*.json"))
    cycle = json.loads(cycle_file.read_text(encoding="utf-8"))
    assert cycle["status"] == "PARTIAL"
    assert cycle["results"] == [{"task_id": "planned_task_0", "status": "NOT_EXECUTED"}]
    assert "no task execution adapter is connected" in cycle["metadata"]["execution_boundary"]
