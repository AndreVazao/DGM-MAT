import os
from pathlib import Path
from typing import Optional
from core.observability.logger import dgm_logger

class RuntimeStorageManager:
    def __init__(self, base_path: Optional[str] = None):
        # Default to C:/DevopsGodMode or equivalent relative if not on Windows
        if not base_path:
            base_path = os.getenv("DGM_STORAGE_PATH")
            if not base_path:
                if os.name == 'nt':
                    base_path = "C:/DevopsGodMode"
                else:
                    base_path = str(Path.home() / "DevopsGodMode")

        self.base_path = Path(base_path)
        self._ensure_structure()

    def _ensure_structure(self):
        subdirs = [
            "data/memory",
            "data/cognition",
            "data/governance",
            "data/federation",
            "data/sandbox",
            "data/snapshots",
            "data/logs"
        ]
        for subdir in subdirs:
            (self.base_path / subdir).mkdir(parents=True, exist_ok=True)
        dgm_logger.info(f"StorageManager: Initialized at {self.base_path}")

    def get_path(self, domain: str, filename: str) -> Path:
        """Returns a normalized path for a specific storage domain."""
        safe_domains = {
            "memory": "data/memory",
            "cognition": "data/cognition",
            "governance": "data/governance",
            "federation": "data/federation",
            "sandbox": "data/sandbox",
            "snapshots": "data/snapshots",
            "logs": "data/logs"
        }

        if domain not in safe_domains:
            domain = "data/temp"
            (self.base_path / domain).mkdir(parents=True, exist_ok=True)
        else:
            domain = safe_domains[domain]

        return self.base_path / domain / filename

    def save_data(self, domain: str, filename: str, content: str):
        path = self.get_path(domain, filename)
        path.write_text(content)
        dgm_logger.debug(f"StorageManager: Saved {filename} to {domain}")

    def read_data(self, domain: str, filename: str) -> Optional[str]:
        path = self.get_path(domain, filename)
        if path.exists():
            return path.read_text()
        return None
