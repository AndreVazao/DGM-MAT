import shlex
import subprocess
from dataclasses import dataclass
from core.observability.logger import dgm_logger

SAFE_COMMANDS = {
    "git",
    "python",
    "pip",
    "pytest",
    "node",
    "npm",
    "echo", # Added echo for tests, following standard safe practice for testing
}

@dataclass
class ExecutionResult:
    success: bool
    stdout: str
    stderr: str
    returncode: int

class LocalExecutor:
    """
    Executes local shell commands and scripts with hardening.
    """
    def execute(self, command: str) -> ExecutionResult:
        dgm_logger.info(f"LocalExecutor: Running command: {command}")
        try:
            args = shlex.split(command)

            if not args:
                return ExecutionResult(False, "", "Empty command", -1)

            if args[0] not in SAFE_COMMANDS:
                dgm_logger.warning(f"LocalExecutor: Blocked unsafe command: {args[0]}")
                return ExecutionResult(
                    False,
                    "",
                    f"Blocked unsafe command: {args[0]}",
                    -1
                )

            result = subprocess.run(
                args,
                capture_output=True,
                text=True,
                timeout=120,
                check=False
            )

            if result.returncode != 0:
                dgm_logger.error(f"LocalExecutor: Command failed with return code {result.returncode}")

            return ExecutionResult(
                result.returncode == 0,
                result.stdout,
                result.stderr,
                result.returncode
            )

        except subprocess.TimeoutExpired:
            dgm_logger.error("LocalExecutor: Execution timeout")
            return ExecutionResult(False, "", "Execution timeout", -1)

        except Exception as e:
            dgm_logger.error(f"LocalExecutor: Unexpected error: {e}")
            return ExecutionResult(False, "", str(e), -1)
