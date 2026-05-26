from cockpit.app import run_cockpit
from core.observability.logger import dgm_logger

def start():
    dgm_logger.info("Phase 37: Starting Cockpit...")
    run_cockpit()

if __name__ == "__main__":
    start()
