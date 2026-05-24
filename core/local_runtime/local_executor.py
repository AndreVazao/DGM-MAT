import subprocess
from core.observability.logger import dgm_logger

class LocalExecutor:
    """
    Executes local shell commands and scripts.
    """
    def execute(self, command: str) -> str:
        dgm_logger.info(f"LocalExecutor: Running command: {command}")
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True, check=True)
            return result.stdout
        except subprocess.CalledProcessError as e:
            dgm_logger.error(f"LocalExecutor: Command failed: {e.stderr}")
            return f"Error: {e.stderr}"
