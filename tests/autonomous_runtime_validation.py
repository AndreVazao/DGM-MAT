import sys
import os
from pathlib import Path
from core.local_runtime.local_executor import LocalExecutor
from core.local_runtime.process_supervisor import ProcessSupervisor
from core.observability.logger import dgm_logger

def validate():
    dgm_logger.info("Validating Autonomous Runtime...")
    executor = LocalExecutor()
    supervisor = ProcessSupervisor()

    # Test executor
    res = executor.execute("echo 'Hello from LocalExecutor'")
    if "Hello" in res:
        dgm_logger.info("LocalExecutor: SUCCESS")
    else:
        dgm_logger.error("LocalExecutor: FAILED")
        return False

    # Test supervisor
    supervisor.monitor_processes()
    dgm_logger.info("ProcessSupervisor: SUCCESS")

    return True

if __name__ == "__main__":
    if validate():
        print("AUTONOMOUS RUNTIME VALIDATION: PASSED")
    else:
        print("AUTONOMOUS RUNTIME VALIDATION: FAILED")
        sys.exit(1)
