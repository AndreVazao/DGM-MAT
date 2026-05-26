import pytest
from core.execution_fabric.worktree_runtime import WorktreeRuntime

def test_isolated_worktree_execution():
    runtime = WorktreeRuntime(base_path="test_worktrees")
    # Note: requires git repo context to work fully
    # We test the interface hardening here
    result = runtime.execute_in_worktree("non_existent", ["ls"])
    assert result is None # Should fail gracefully
