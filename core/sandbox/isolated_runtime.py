"""Fail-closed adapter over the bounded Git worktree validation runtime."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Sequence

from core.execution_fabric.worktree_runtime import WorktreeRuntime


class IsolatedRuntime:
    """Compatibility adapter; this is Git isolation, not OS process sandboxing."""

    def __init__(self, worktree_runtime: WorktreeRuntime | None = None):
        self.worktree_runtime = worktree_runtime or WorktreeRuntime()
        self.active_processes: dict[str, Any] = {}

    def create_sandbox(self, task_id: str) -> str:
        worktree_path = self.worktree_runtime.create_sandbox(task_id)
        if worktree_path is None:
            raise RuntimeError("Unable to create a registered isolated Git worktree; no temporary-directory fallback is allowed.")
        return str(worktree_path)

    def run_safe(self, sandbox_path: str, command: Sequence[str], task_id: str) -> dict[str, Any]:
        """Delegate only fixed validation commands to WorktreeRuntime."""
        if not isinstance(task_id, str):
            return {"status": "rejected", "error": "Invalid task ID."}
        branch_name = f"dgm-sandbox-{task_id}"
        try:
            expected = self.worktree_runtime._target_for(branch_name)
            supplied = Path(sandbox_path).expanduser().resolve()
            if not supplied.exists() or not supplied.samefile(expected):
                return {"status": "rejected", "error": "Sandbox path does not match the registered task worktree."}
        except (OSError, ValueError):
            return {"status": "rejected", "error": "Sandbox path is invalid or not registered."}

        result = self.worktree_runtime.execute_in_worktree(branch_name, command)
        if result is None:
            return {"status": "rejected", "error": "Command is outside the bounded validation catalogue or the worktree is unavailable."}
        status = "timeout" if result.returncode == 124 else "success" if result.returncode == 0 else "failed"
        return {
            "status": status,
            "exit_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }

    def terminate_task(self, task_id: str) -> bool:
        # Validation currently runs synchronously; there is no detached process handle.
        return False

    def rollback_sandbox(self, task_id: str) -> bool:
        return self.worktree_runtime.cleanup_sandbox(task_id)
