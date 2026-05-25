from core.observability.logger import dgm_logger

class DegradedModeRouter:
    """
    Routes system operations to degraded modes when subsystems fail.
    """
    def __init__(self):
        self.active_degradations = set()

    def activate_degraded_mode(self, module: str):
        dgm_logger.critical(f"DegradedModeRouter: Activating degraded mode for '{module}'")
        self.active_degradations.add(module)

    def is_module_active(self, module: str) -> bool:
        return module not in self.active_degradations
