import subprocess
import os
import signal
import sys
import tempfile
from typing import Dict, Any, Optional, List
from pathlib import Path
from core.observability.logger import dgm_logger
from core.execution_fabric.worktree_runtime import WorktreeRuntime
from core.sandbox.execution_limits import ExecutionLimits

class IsolatedRuntime:
    """Provides secure and isolated execution environments for autonomous tasks."""
    def __init__(self):
        self.worktree_runtime = WorktreeRuntime()
        self.limits = ExecutionLimits()
        self.active_processes: Dict[str, subprocess.Popen] = {}

    def create_sandbox(self, task_id: str) -> str:
        dgm_logger.info(f"IsolatedRuntime: Creating secure sandbox for task {task_id}")
        # Use task_id as branch name for worktree isolation
        worktree_path = self.worktree_runtime.create_worktree(f"sandbox_{task_id}")
        if worktree_path:
            return str(worktree_path)

        # Fallback to system temp directory (Phase 39 Bandit Fix)
        temp_base = tempfile.gettempdir()
        fallback_path = os.path.join(temp_base, f"dgm_sandbox_{task_id}")
        os.makedirs(fallback_path, exist_ok=True)
        return fallback_path

    def run_safe(self, sandbox_path: str, command: List[str], task_id: str) -> Dict[str, Any]:
        """
        Executes a command safely using list-based subprocess to avoid shell=True vulnerabilities.
        """
        dgm_logger.info(f"IsolatedRuntime: Executing command safely in {sandbox_path}")

        try:
            # Use process group creation only on Unix-like systems
            kwargs = {}
            if sys.platform != "win32":
                kwargs["preexec_fn"] = os.setsid

            process = subprocess.Popen(
                command,
                shell=False, # HARD REQUIREMENT: No shell=True
                cwd=sandbox_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                **kwargs
            )
            self.active_processes[task_id] = process

            # Simplified timeout/limit enforcement
            stdout, stderr = process.communicate(timeout=300) # 5 min limit

            status = "success" if process.returncode == 0 else "failed"
            return {
                "status": status,
                "exit_code": process.returncode,
                "stdout": stdout,
                "stderr": stderr
            }
        except subprocess.TimeoutExpired:
            dgm_logger.error(f"IsolatedRuntime: Task {task_id} timed out. Terminating...")
            self.terminate_task(task_id)
            return {"status": "timeout", "error": "Execution exceeded time limit."}
        except Exception as e:
            dgm_logger.error(f"IsolatedRuntime: Execution error: {e}")
            return {"status": "error", "error": str(e)}
        finally:
            if task_id in self.active_processes:
                del self.active_processes[task_id]

    def terminate_task(self, task_id: str):
        if task_id in self.active_processes:
            process = self.active_processes[task_id]
            if sys.platform != "win32":
                try:
                    os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                except (ProcessLookupError, PermissionError):
                    pass
            else:
                process.terminate()
            dgm_logger.info(f"IsolatedRuntime: Terminated runaway task {task_id}")

    def rollback_sandbox(self, task_id: str):
        dgm_logger.warning(f"IsolatedRuntime: Rolling back changes for {task_id}")
        self.worktree_runtime.remove_worktree(f"sandbox_{task_id}")
