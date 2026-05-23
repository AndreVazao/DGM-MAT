from core.execution.branch_manager import BranchManager
from core.execution.merge_guard import MergeGuard

def test_branch_generation():
    branch = BranchManager.generate_branch_name("test-agent", "task-123")
    assert branch == "agent/test-agent/task-123"

def test_merge_guard():
    assert MergeGuard.can_merge("feature/branch") is True
    assert MergeGuard.can_merge("main") is False
