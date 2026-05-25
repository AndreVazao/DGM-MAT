import subprocess
from typing import List, Optional
from core.observability.logger import dgm_logger

class SafeAutonomousExecutor:
    """
    Hardened executor with safety guards.
    Prevents arbitrary shell command execution and enforces validation.
    """
    def __init__(self, mode: str = "SAFE"):
        self.mode = mode
        self.allowed_commands = ["git", "pytest", "python", "pip"]

    def execute_command(self, cmd: List[str], cwd: Optional[str] = None, timeout: int = 300):
        if not cmd: return

        # Guard 1: Prohibit string commands (forces list for subprocess)
        if isinstance(cmd, str):
            raise SecurityError("Arbitrary shell strings are prohibited")

        # Guard 2: Command Whitelist
        base_cmd = cmd[0]
        if base_cmd not in self.allowed_commands:
            raise SecurityError(f"Command '{base_cmd}' is not in the allowed safety whitelist")

        # Guard 3: Mode enforcement
        if self.mode == "SAFE" and "rm" in cmd:
             raise SecurityError("Deletions are prohibited in SAFE mode")

        dgm_logger.info(f"SafeExecutor: Executing {cmd}")
        try:
            return subprocess.run(
                cmd,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=timeout,
                shell=False # HARD REQUIREMENT: No shell=True
            )
        except subprocess.TimeoutExpired:
            dgm_logger.error(f"SafeExecutor: Timeout exceeded for {cmd}")
            raise

class SecurityError(Exception):
    pass
