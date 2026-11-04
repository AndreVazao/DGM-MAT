from unittest.mock import Mock

from core.execution_fabric.autonomous_executor import AutonomousExecutor


def _executor_with_mocks():
    executor = AutonomousExecutor()
    executor.runtime = Mock()
    executor.runtime.create_sandbox.return_value = "C:/isolated/worktree"
    executor.patch_engine = Mock()
    executor.supervisor = Mock()
    executor.supervisor.validate_plan.return_value = True
    return executor


def test_autonomous_executor_does_not_report_success_without_a_real_patch():
    executor = _executor_with_mocks()
    executor.patch_engine.generate_patch.return_value = ""

    result = executor.execute_task({"id": "mission_empty", "goal": "Implement a real change"})

    assert result is False
    executor.patch_engine.apply_patch.assert_not_called()
    executor.runtime.cleanup_sandbox.assert_called_once_with("mission_empty")


def test_autonomous_executor_never_reapplies_diff_to_primary_repository():
    executor = _executor_with_mocks()
    executor.patch_engine.generate_patch.return_value = "diff --git a/a.py b/a.py"
    executor.patch_engine.assess_risk.return_value = {
        "score": 0.1, "level": "LOW", "warnings": [], "is_blocked": False
    }
    executor.supervisor.authorize_commit.return_value = True

    result = executor.execute_task({"id": "mission_patch", "goal": "Prepare a bounded code change"})

    assert result is False
    executor.patch_engine.apply_patch.assert_not_called()
    executor.runtime.cleanup_sandbox.assert_called_once_with("mission_patch")


def test_autonomous_executor_does_not_cleanup_worktree_it_failed_to_create():
    executor = _executor_with_mocks()
    executor.runtime.create_sandbox.return_value = None

    result = executor.execute_task({"id": "mission_existing", "goal": "Inspect existing task"})

    assert result is False
    executor.runtime.cleanup_sandbox.assert_not_called()
