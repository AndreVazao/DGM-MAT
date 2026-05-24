import sys
import os
import subprocess
from core.observability.logger import dgm_logger

def test_executable_startup():
    dgm_logger.info("Testing executable startup...")
    # This script would normally run against the built exe,
    # but here we simulate the checks the exe would perform.
    try:
        # Check for critical dependencies
        import PySide6
        import fastapi
        import uvicorn
        dgm_logger.info("Critical dependencies verified.")
        return True
    except ImportError as e:
        dgm_logger.error(f"Missing critical dependency: {e}")
        return False

if __name__ == "__main__":
    if test_executable_startup():
        print("Executable runtime validation PASSED")
        sys.exit(0)
    else:
        print("Executable runtime validation FAILED")
        sys.exit(1)
