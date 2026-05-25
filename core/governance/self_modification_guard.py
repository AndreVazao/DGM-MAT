from typing import List
from core.observability.logger import dgm_logger

class SelfModificationGuard:
    """
    Prevents autonomous modifications to core runtime and safeguards.
    """
    PROTECTED_PATHS = [
        "core/runtime/",
        "core/governance/",
        "core/validation/",
        "shared/config/",
        "scripts/autostart/"
    ]

    def is_modification_allowed(self, file_path: str) -> bool:
        """
        Checks if the file path is protected from autonomous modification.
        """
        for protected in self.PROTECTED_PATHS:
            if file_path.startswith(protected):
                dgm_logger.warning(f"SelfModificationGuard: Autonomous modification of {file_path} is FORBIDDEN.")
                return False
        return True
