"""Legacy update facade with explicit fail-closed behavior.

The supported Windows update path is currently the reviewed PowerShell installer
and rollback scripts. This facade is not connected to a release downloader or
staged updater, so it must never report that an update was applied.
"""
from typing import Any, Dict, Optional

from core.observability.logger import dgm_logger


class UpdateEngine:
    """Compatibility facade; release discovery and application are not implemented."""

    def __init__(self) -> None:
        self.current_version = "0.1.0"
        dgm_logger.info(
            "Update Engine: Initialized in fail-closed compatibility mode. "
            "Current version metadata is not authoritative."
        )

    def check_for_updates(self) -> Optional[Dict[str, Any]]:
        """Return no candidate until a verified release checker is connected."""
        dgm_logger.warning(
            "Update Engine: Release discovery is unavailable; no update was checked."
        )
        return None

    def apply_update(self, version: str) -> bool:
        """Refuse to claim success until a verified staged updater is implemented."""
        dgm_logger.warning(
            "Update Engine: Refusing to apply %s; the staged updater is not implemented.",
            version,
        )
        return False
