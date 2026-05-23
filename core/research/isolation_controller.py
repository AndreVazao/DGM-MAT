from core.observability.logger import dgm_logger

class IsolationController:
    def prepare_sandbox(self, isolation_id: str) -> bool:
        dgm_logger.info(f"Preparing isolation namespace: {isolation_id}")
        return True

    def cleanup(self, isolation_id: str):
        dgm_logger.info(f"Cleaning up isolation namespace: {isolation_id}")
