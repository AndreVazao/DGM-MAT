import subprocess
import os
from pathlib import Path
from typing import List, Optional, Dict, Any
from core.observability.logger import dgm_logger

def run_git_command(args: List[str], cwd: Optional[Path] = None, timeout: int = 120) -> subprocess.CompletedProcess:
    """
    Executes a git command with detailed logging and error handling.
    """
    cmd = ["git"] + args
    cwd_str = str(cwd) if cwd else os.getcwd()

    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout
        )

        if result.returncode != 0:
            dgm_logger.error(
                f"Git command failed in {cwd_str}: {cmd}\n"
                f"STDOUT: {result.stdout}\n"
                f"STDERR: {result.stderr}"
            )
        else:
            dgm_logger.debug(f"Git command success: {cmd}")

        return result

    except subprocess.TimeoutExpired:
        dgm_logger.error(f"Git command timed out after {timeout}s: {cmd}")
        raise
    except Exception as e:
        dgm_logger.error(f"Error executing git command {cmd}: {e}")
        raise

def branch_exists(branch_name: str, cwd: Optional[Path] = None) -> bool:
    """Checks if a git branch exists."""
    result = run_git_command(["branch", "--list", branch_name], cwd=cwd)
    return branch_name in result.stdout

def ensure_branch(branch_name: str, cwd: Optional[Path] = None):
    """Ensures a branch exists, creating it if it doesn't."""
    if not branch_exists(branch_name, cwd):
        run_git_command(["checkout", "-b", branch_name], cwd=cwd)
    else:
        run_git_command(["checkout", branch_name], cwd=cwd)
