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
        Strict separation between source code and runtime data.
        """
        if not base_path:
            # 1. Check for specific storage path env var
            base_path = os.getenv("DGM_STORAGE_PATH")

            if not base_path:
                # 2. Check for base path env var
                dgm_base = os.getenv("DGM_BASE_PATH")
                if dgm_base:
                    base_path = str(Path(dgm_base) / "data")
                else:
                    # 3. Default to a gitignored local runtime directory
                    project_root = Path(__file__).parent.parent.parent
                    base_path = str(project_root / "storage" / "runtime")

        self.base_path = Path(base_path).resolve()
        self._fallback_path: Optional[Path] = None
        self._ensure_structure()

    def _ensure_structure(self):
        """Creates the necessary directory structure for runtime data with self-healing."""
        subdirs = [
            "memory",
            "cognition",
            "governance",
            "federation",
            "sandbox",
            "snapshots",
            "logs",
            "sessions",
            "temp",
            "corrupted"
        ]
        try:
            # Check if base_path is writable if it exists, or check if parent is writable
            target = self.base_path if self.base_path.exists() else self.base_path.parent
            if target.exists() and not os.access(target, os.W_OK):
                dgm_logger.warning(f"StorageManager: Path {target} is not writable. Attempting degraded mode.")
                return

            self.base_path.mkdir(parents=True, exist_ok=True)

            for subdir in subdirs:
                (self.base_path / subdir).mkdir(parents=True, exist_ok=True)

            dgm_logger.info(f"StorageManager: Initialized at {self.base_path}")
        except Exception as e:
            dgm_logger.error(f"StorageManager: Failed to initialize structure at {self.base_path}: {e}")

    def get_path(self, domain: str, filename: Optional[str] = None) -> Path:
        """Returns a normalized, OS-safe path for a specific storage domain."""
        safe_domains = {
            "memory": "memory",
            "cognition": "cognition",
            "governance": "governance",
            "federation": "federation",
            "sandbox": "sandbox",
            "snapshots": "snapshots",
            "logs": "logs",
            "sessions": "sessions",
            "temp": "temp",
            "corrupted": "corrupted"
        }

        domain_path = safe_domains.get(domain, "temp")
        target_dir = self.base_path / domain_path

        try:
            if not target_dir.exists():
                target_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            # Fallback to a secure temporary directory in case of permission issues
            if not self._fallback_path:
                self._fallback_path = Path(tempfile.mkdtemp(prefix="dgm_fallback_"))
                dgm_logger.warning(f"StorageManager: Falling back to secure temp directory: {self._fallback_path}")

            target_dir = self._fallback_path / domain_path
            target_dir.mkdir(parents=True, exist_ok=True)

        if filename:
            # Basic sanitization for filenames
            safe_filename = "".join(c for c in filename if c.isalnum() or c in "._-").strip()
            return target_dir / safe_filename

        return target_dir

    def isolate_corrupted(self, domain: str, filename: str):
        """Moves a corrupted file to the 'corrupted' domain for analysis."""
        source_path = self.get_path(domain, filename)
        if not source_path.exists():
            return

        dest_path = self.get_path("corrupted", f"{domain}_{filename}")
        try:
            shutil.move(str(source_path), str(dest_path))
            dgm_logger.warning(f"StorageManager: Isolated corrupted file {filename} from {domain} to corrupted storage.")
        except Exception as e:
            dgm_logger.error(f"StorageManager: Failed to isolate corrupted file: {e}")

    def save_data(self, domain: str, filename: str, content: str):
        """Saves content to a file within a domain."""
        path = self.get_path(domain, filename)
        try:
            path.write_text(content, encoding="utf-8")
            dgm_logger.debug(f"StorageManager: Saved {filename} to {domain}")
        except Exception as e:
            dgm_logger.error(f"StorageManager: Failed to save data to {path}: {e}")

    def read_data(self, domain: str, filename: str) -> Optional[str]:
        """Reads content from a file within a domain."""
        path = self.get_path(domain, filename)
        if path.exists():
            try:
                return path.read_text(encoding="utf-8")
            except Exception as e:
                dgm_logger.error(f"StorageManager: Failed to read data from {path}: {e}")
                self.isolate_corrupted(domain, filename)
        return None

# Singleton instance for system-wide use
storage_manager = RuntimeStorageManager()
