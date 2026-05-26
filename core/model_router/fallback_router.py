from core.observability.logger import dgm_logger

class FallbackRouter:
    def get_fallback(self, failed_model_id: str) -> str:
        dgm_logger.warning(f"FallbackRouter: Model {failed_model_id} failed. Selecting fallback.")
        return "gpt-4o-mini" # Default safe fallback
