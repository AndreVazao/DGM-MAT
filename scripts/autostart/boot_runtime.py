from core.lifecycle.bootstrap_engine import BootstrapEngine
from core.observability.logger import dgm_logger

def boot():
    dgm_logger.info("Phase 37: Booting DGM-MAT Runtime...")
    bootstrap = BootstrapEngine()
    bootstrap.prepare()
    dgm_logger.info("Runtime Boot Complete.")

if __name__ == "__main__":
    boot()
