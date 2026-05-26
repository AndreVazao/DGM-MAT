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
        worktree_path = self.worktree_runtime.create_worktree(f"sandbox_{task_id}")
        if worktree_path:
            return str(worktree_path)

        # Phase 39 Bandit Fix
        temp_base = tempfile.gettempdir()
        fallback_path = os.path.join(temp_base, f"dgm_sandbox_{task_id}")
        os.makedirs(fallback_path, exist_ok=True)
        return fallback_path

    def run_safe(self, sandbox_path: str, command: List[str], task_id: str) -> Dict[str, Any]:
        dgm_logger.info(f"IsolatedRuntime: Executing command safely in {sandbox_path}")
        try:
            kwargs = {}
            if sys.platform != "win32":
                kwargs["preexec_fn"] = os.setsid

            process = subprocess.Popen(
                command,
                shell=False,
                cwd=sandbox_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                **kwargs
            )
            self.active_processes[task_id] = process
            stdout, stderr = process.communicate(timeout=300)
            status = "success" if process.returncode == 0 else "failed"
            return {"status": status, "exit_code": process.returncode, "stdout": stdout, "stderr": stderr}
        except subprocess.TimeoutExpired:
            self.terminate_task(task_id)
            return {"status": "timeout", "error": "Execution exceeded time limit."}
        except Exception as e:
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
                except Exception: pass
            else:
                process.terminate()

    def rollback_sandbox(self, task_id: str):
        self.worktree_runtime.remove_worktree(f"sandbox_{task_id}")
