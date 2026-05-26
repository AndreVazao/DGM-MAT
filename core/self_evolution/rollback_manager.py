from core.observability.logger import dgm_logger

class RollbackManager:
    """Manages system rollbacks in case of failed self-evolution."""
    def __init__(self):
        pass

    def perform_rollback(self, failed_module: str):
        dgm_logger.warning(f"RollbackManager: Rolling back failed evolution for {failed_module}")
