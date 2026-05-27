import os
import shutil
import tempfile
from pathlib import Path
from typing import Optional
from core.observability.logger import dgm_logger

class RuntimeStorageManager:
    def __init__(self, base_path: Optional[str] = None):
        """
        Initializes the RuntimeStorageManager with a dynamic base path.
        PHASE 42.1: Uses canonical persistent absolute directories.
        """
        if not base_path:
            base_path = os.getenv("DGM_STORAGE_PATH")

            if not base_path:
                dgm_base = os.getenv("DGM_BASE_PATH")
                if dgm_base:
                    base_path = str(Path(dgm_base) / "runtime")
                else:
                    if os.name == 'nt':
                        # Requirement 1 & 2: Canonical Windows paths
                        base_path = "C:\\DevopGodMode\\runtime"
                    else:
                        project_root = Path(__file__).parent.parent.parent
                        base_path = str(project_root / "storage" / "runtime")

        self.base_path = Path(base_path).resolve()
        self._fallback_path: Optional[Path] = None
        self._ensure_structure()

    def _ensure_structure(self):
        """Creates the necessary directory structure for runtime data."""
        subdirs = [
            "memory", "cognition", "governance", "federation",
            "sandbox", "snapshots", "graphs", "patterns", "roadmaps",
            "evolution_memory", "provider_knowledge", "tasks", "logs",
            "sessions", "temp", "corrupted", "missions"
        ]
        try:
            # Attempt to create the base path (Requirement 1: Automatically create)
            try:
                self.base_path.mkdir(parents=True, exist_ok=True)
            except (PermissionError, OSError):
                if not self._fallback_path:
                    self._fallback_path = Path(tempfile.mkdtemp(prefix="dgm_fallback_"))
                    dgm_logger.warning(f"StorageManager: Falling back to {self._fallback_path} due to permission issues.")
                self.base_path = self._fallback_path

            for subdir in subdirs:
                (self.base_path / subdir).mkdir(parents=True, exist_ok=True)

            dgm_logger.info(f"StorageManager: Operational at {self.base_path}")
        except Exception as e:
            dgm_logger.error(f"StorageManager: Failed to initialize structure: {e}")

    def get_path(self, domain: str, filename: Optional[str] = None) -> Path:
        safe_domains = {
            "memory": "memory", "cognition": "cognition", "governance": "governance",
            "federation": "federation", "sandbox": "sandbox", "snapshots": "snapshots",
            "graphs": "graphs", "patterns": "patterns", "roadmaps": "roadmaps",
            "evolution_memory": "evolution_memory", "provider_knowledge": "provider_knowledge",
            "tasks": "tasks", "logs": "logs", "sessions": "sessions", "temp": "temp",
            "corrupted": "corrupted", "missions": "missions"
        }
        domain_path = safe_domains.get(domain, "temp")
        target_dir = self.base_path / domain_path
        if not target_dir.exists():
            target_dir.mkdir(parents=True, exist_ok=True)
        if filename:
            safe_filename = "".join(c for c in filename if c.isalnum() or c in "._-").strip()
            return target_dir / safe_filename
        return target_dir

    def isolate_corrupted(self, domain: str, filename: str):
        source_path = self.get_path(domain, filename)
        if not source_path.exists(): return
        dest_path = self.get_path("corrupted", f"{domain}_{filename}")
        try:
            shutil.move(str(source_path), str(dest_path))
            dgm_logger.warning(f"StorageManager: Isolated corrupted file {filename}")
        except Exception: pass

    def save_data(self, domain: str, filename: str, content: str):
        path = self.get_path(domain, filename)
        try: path.write_text(content, encoding="utf-8")
        except Exception: pass

    def read_data(self, domain: str, filename: str) -> Optional[str]:
        path = self.get_path(domain, filename)
        if path.exists():
            try: return path.read_text(encoding="utf-8")
            except Exception: self.isolate_corrupted(domain, filename)
        return None

storage_manager = RuntimeStorageManager()
