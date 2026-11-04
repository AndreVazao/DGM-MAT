from __future__ import annotations

from unittest.mock import Mock

from core.execution_fabric.execution_supervisor import ExecutionSupervisor


def test_execution_supervisor_rejects_unbounded_or_incomplete_plans():
    supervisor = ExecutionSupervisor()

    assert supervisor.validate_plan(None) is False
    assert supervisor.validate_plan({"id": "task-1"}) is False
    assert supervisor.validate_plan({"id": "../escape", "goal": "Review code"}) is False
    assert supervisor.validate_plan({"id": "task-1", "goal": "Review code", "command": "whoami"}) is False
    assert supervisor.validate_plan({"id": "task-1", "goal": "Review code", "approval_required": "yes"}) is False


def test_execution_supervisor_accepts_metadata_only_plan():
    supervisor = ExecutionSupervisor()

    assert supervisor.validate_plan({
        "id": "mission_123",
        "goal": "Improve a bounded test report",
        "approval_required": True,
    }) is True


def test_execution_supervisor_persists_risk_metadata_for_approval(monkeypatch):
    supervisor = ExecutionSupervisor()
    request = Mock()
    monkeypatch.setattr(
        "core.execution_fabric.execution_supervisor.approval_manager.request_approval",
        request,
    )

    allowed = supervisor.authorize_commit(
        "diff --git a/a.py b/a.py",
        "mission_123",
        True,
        risk_score=0.85,
        impact="HIGH",
    )

    assert allowed is False
    request.assert_called_once_with("mission_123", "diff --git a/a.py b/a.py", 0.85, "HIGH")


def test_execution_supervisor_does_not_authorize_empty_patch():
    supervisor = ExecutionSupervisor()

    assert supervisor.authorize_commit("", "mission_123", False) is False


def test_execution_supervisor_rejects_invalid_risk_metadata():
    supervisor = ExecutionSupervisor()

    assert supervisor.authorize_commit(
        "diff --git a/a.py b/a.py", "mission_123", True,
        risk_score=float("nan"), impact="HIGH",
    ) is False
    assert supervisor.authorize_commit(
        "diff --git a/a.py b/a.py", "mission_123", True,
        risk_score=1.5, impact="HIGH",
    ) is False
    assert supervisor.authorize_commit(
        "diff --git a/a.py b/a.py", "mission_123", True,
        risk_score=0.5, impact="UNKNOWN",
    ) is False
    assert supervisor.authorize_commit(
        "diff --git a/a.py b/a.py", "mission_123", "yes",
        risk_score=0.5, impact="LOW",
    ) is False
