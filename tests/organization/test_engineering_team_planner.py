from __future__ import annotations

import pytest

from core.organization.engineering_team_planner import EngineeringTeamPlanner


def build(**overrides):
    values = {
        "mission_id": "mission:demo",
        "title": "Add API feature",
        "description": "Implement and verify a bounded API change.",
        "changed_paths": ["core/api/routes.py", "cockpit/src/app.tsx"],
    }
    values.update(overrides)
    return EngineeringTeamPlanner().build_plan(**values)


def test_mixed_language_plan_creates_specialists_and_independent_teams():
    plan = build()
    assert plan.status == "PLAN_ONLY"
    assert plan.language_ids == ("python", "typescript")
    stages = [task.metadata["team_stage"] for task in plan.tasks]
    assert stages.count("implementation") == 2
    assert "integration-review" in stages
    assert "bug-hunt" in stages
    assert "qa" in stages


def test_implementation_tasks_are_not_execution_authority():
    plan = build()
    implementations = [t for t in plan.tasks if t.metadata["team_stage"] == "implementation"]
    assert implementations
    for task in implementations:
        assert task.owner_department is None
        assert task.metadata["planning_only"] is True
        assert task.metadata["execution_authorized"] is False
        assert task.metadata["toolchain_status"] == "not_probed"
        assert task.approval_required is True
        assert "repo:write:sandbox" in task.metadata["required_permissions"]


def test_integration_and_quality_tasks_depend_on_all_implementations():
    plan = build()
    implementations = {t.task_id for t in plan.tasks if t.metadata["team_stage"] == "implementation"}
    integration = next(t for t in plan.tasks if t.metadata["team_stage"] == "integration-review")
    assert set(integration.dependencies) == implementations
    assert integration.owner_department is None
    for stage in ("bug-hunt", "qa"):
        review = next(t for t in plan.tasks if t.metadata["team_stage"] == stage)
        assert review.dependencies == [integration.task_id]


def test_research_precedes_implementation_when_requested():
    plan = build(include_research=True)
    research = next(t for t in plan.tasks if t.metadata["team_stage"] == "research")
    for task in plan.tasks:
        if task.metadata["team_stage"] == "implementation":
            assert task.dependencies == [research.task_id]


def test_high_risk_plan_adds_independent_security_review():
    plan = build(risk_level="critical")
    security = next(t for t in plan.tasks if t.metadata["team_stage"] == "security-review")
    integration = next(t for t in plan.tasks if t.metadata["team_stage"] == "integration-review")
    assert security.dependencies == [integration.task_id]
    assert security.metadata["independent_review"] is True


def test_unknown_and_ambiguous_paths_are_reported_not_assigned():
    plan = build(changed_paths=["src/app.py", "include/shared.h", "unknown.file"])
    assert plan.status == "PARTIAL"
    assert plan.language_ids == ("python",)
    assert "include/shared.h" in plan.blocked_paths
    assert "unknown.file" in plan.blocked_paths
    assert plan.recognized_paths == ("src/app.py",)
    assert all("shared.h" not in path for task in plan.tasks for path in task.inputs)


def test_unsafe_paths_are_blocked():
    plan = build(changed_paths=["../outside.py", "/root/secret.py", "C:\\Windows\\system.ps1", "safe/module.py"])
    assert plan.status == "PARTIAL"
    assert "safe/module.py" in plan.recognized_paths
    assert "../outside.py" in plan.blocked_paths
    assert "/root/secret.py" in plan.blocked_paths
    assert "C:\\Windows\\system.ps1" in plan.blocked_paths


def test_duplicate_paths_are_deduplicated_case_insensitively():
    plan = build(changed_paths=["src/App.py", "src/app.PY"])
    implementation = next(t for t in plan.tasks if t.metadata["team_stage"] == "implementation")
    assert implementation.inputs == ["src/App.py"]


def test_task_ids_are_stable_for_identical_input():
    first = build()
    second = build()
    assert [t.task_id for t in first.tasks] == [t.task_id for t in second.tasks]


def test_task_ids_change_with_mission():
    first = build(mission_id="mission:one")
    second = build(mission_id="mission:two")
    assert first.tasks[0].task_id != second.tasks[0].task_id


def test_no_unambiguous_paths_blocks_plan_without_tasks():
    plan = build(changed_paths=["include/common.h", "README", "../outside.py"])
    assert plan.status == "BLOCKED"
    assert plan.tasks == ()


@pytest.mark.parametrize("risk", ["unknown", "", None])
def test_invalid_risk_level_is_rejected(risk):
    with pytest.raises(ValueError):
        build(risk_level=risk)


def test_required_fields_are_validated():
    with pytest.raises(ValueError):
        build(mission_id=" ")
    with pytest.raises(ValueError):
        build(title="")
    with pytest.raises(ValueError):
        build(description=" ")


def test_changed_paths_must_be_an_iterable_not_a_single_string():
    with pytest.raises(TypeError):
        build(changed_paths="src/main.py")

def test_generated_safety_metadata_cannot_be_overridden():
    task = EngineeringTeamPlanner._task(
        "mission:locked",
        "implementation",
        "Unsafe override attempt",
        "Test invariant protection.",
        metadata={
            "planning_only": False,
            "execution_authorized": True,
            "toolchain_status": "available",
            "team_stage": "execution",
            "required_skills": ["arbitrary"],
        },
    )
    assert task.metadata["planning_only"] is True
    assert task.metadata["execution_authorized"] is False
    assert task.metadata["toolchain_status"] == "not_probed"
    assert task.metadata["team_stage"] == "implementation"
    assert task.metadata["required_skills"] == []
