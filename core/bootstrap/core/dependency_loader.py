import importlib
from core.observability.logger import dgm_logger

class DependencyLoader:
    @staticmethod
    def validate_dependency(module_name: str, critical: bool = False):
        try:
            importlib.import_module(module_name)
            return True
        except ImportError:
            if critical:
                dgm_logger.critical(f"DependencyLoader: Critical dependency '{module_name}' missing!")
                raise
            dgm_logger.warning(f"DependencyLoader: Optional dependency '{module_name}' missing.")
            return False
