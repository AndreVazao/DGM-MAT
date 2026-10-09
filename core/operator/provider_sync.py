# Path: C:\ProgramasGodMode\DGM-MAT\core\operator\provider_sync.py

from core.observability.logger import dgm_logger


class ProviderSync:
    """
    Deprecated compatibility facade.

    The previous provider-sync implementation depended on missing adapter methods
    and could log apparent outcomes without performing verified synchronization.
    Until a governed, testable sync contract exists, this facade fails closed.
    """

    def sync_providers(self) -> bool:
        dgm_logger.warning(
            "ProviderSync is unavailable: no verified provider synchronization implementation is wired."
        )
        return False
