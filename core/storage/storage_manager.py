import os
import shutil
import tempfile
import sys
import filecmp
import hashlib
import json
from pathlib import Path
from typing import Optional
from core.observability.logger import dgm_logger
from core.runtime.repository_root import resolve_repository_root

class RuntimeStorageManager:
    def __init__(self, base_path: Optional[str] = None):
        """
        Initializes the RuntimeStorageManager with a dynamic base path.
        Strict separation between source code and runtime data.
        """
        use_persistent_default = not base_path and not os.getenv("DGM_STORAGE_PATH") and not os.getenv("DGM_BASE_PATH")
        if not base_path:
            # Explicit overrides remain authoritative for tests, deployments and operators.
            base_path = os.getenv("DGM_STORAGE_PATH")
            if not base_path:
                dgm_base = os.getenv("DGM_BASE_PATH")
                if dgm_base:
                    base_path = str(Path(dgm_base) / "data")
                else:
                    base_path = str(self.default_persistent_path())

        self.base_path = Path(base_path).expanduser().resolve()
        self._fallback_path: Optional[Path] = None
        self._ensure_structure()
        if use_persistent_default:
            legacy_root = resolve_repository_root(__file__) / "storage" / "runtime"
            self._migrate_legacy_runtime(legacy_root)

    @staticmethod
    def default_persistent_path() -> Path:
        """Stable per-user runtime path; never place mutable state beside the executable."""
        local_app_data = os.environ.get("LOCALAPPDATA")
        if local_app_data:
            base = Path(local_app_data)
        else:
            data_home = os.environ.get("XDG_DATA_HOME")
            base = Path(data_home) if data_home else Path.home() / ".local" / "share"
        return (base / "DGM-MAT" / "runtime").expanduser().resolve()

    def _migrate_legacy_runtime(self, legacy_root: Path) -> None:
        """Copy old install-local runtime state without deleting or overwriting either side."""
        try:
            legacy = Path(legacy_root).expanduser().resolve()
            if not legacy.is_dir() or legacy == self.base_path:
                return
            legacy_id = hashlib.sha256(str(legacy).encode("utf-8")).hexdigest()[:12]
            marker = self.base_path / "migration-logs" / f"legacy-runtime-{legacy_id}.json"
            if marker.is_file():
                return

            copied = 0
            conflicts = 0
            for source in sorted(legacy.rglob("*")):
                if source.is_symlink():
                    continue
                relative = source.relative_to(legacy)
                destination = self.base_path / relative
                if source.is_dir():
                    destination.mkdir(parents=True, exist_ok=True)
                    continue
                if not source.is_file():
                    continue
                destination.parent.mkdir(parents=True, exist_ok=True)
                if not destination.exists():
                    shutil.copy2(source, destination)
                    copied += 1
                    continue
                if filecmp.cmp(source, destination, shallow=False):
                    continue

                conflict = self.base_path / "legacy-imports" / legacy_id / relative
                conflict.parent.mkdir(parents=True, exist_ok=True)
                if conflict.exists() and not filecmp.cmp(source, conflict, shallow=False):
                    digest = hashlib.sha256(source.read_bytes()).hexdigest()[:12]
                    conflict = conflict.with_name(f"{conflict.stem}-{digest}{conflict.suffix}")
                if not conflict.exists():
                    shutil.copy2(source, conflict)
                    conflicts += 1

            marker.parent.mkdir(parents=True, exist_ok=True)
            marker.write_text(json.dumps({
                "legacy_root": str(legacy),
                "copied_files": copied,
                "conflict_files_preserved": conflicts,
                "source_retained": True,
            }, indent=2) + "\n", encoding="utf-8")
            dgm_logger.info(
                f"StorageManager: imported {copied} legacy runtime files and preserved "
                f"{conflicts} conflicts from {legacy}"
            )
        except Exception as exc:
            # Do not prevent startup; the old tree remains untouched and the failure is logged.
            dgm_logger.error(
                f"StorageManager: legacy runtime migration failed ({type(exc).__name__}); "
                "the original install-local data was preserved"
            )

    def _ensure_structure(self):
        """Creates the necessary directory structure for runtime data with self-healing."""
        subdirs = [
            "memory", "cognition", "governance", "federation", "sandbox",
            "snapshots", "graphs", "patterns", "roadmaps", "evolution_memory",
            "provider_knowledge", "tasks", "logs", "sessions", "temp",
            "corrupted", "missions"
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

            dgm_logger.info(f"StorageManager: Operational at {self.base_path}")
        except Exception as e:
            # Re-raise for CI fallback tests if necessary, or just log
            dgm_logger.error(f"StorageManager: Failed to initialize structure: {e}")
            raise e

    def get_path(self, domain: str, filename: Optional[str] = None) -> Path:
        """Returns a normalized, OS-safe path for a specific storage domain."""
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
