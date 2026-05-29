import os
import psutil
import time
import platform
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
from core.observability.logger import dgm_logger
from core.ecosystem.ecosystem_registry import EcosystemRegistry
from core.runtime.safe_action_queue import SafeActionQueue
from core.provider_sync.provider_registry import provider_registry
from core.runtime.runtime_profile import detect_runtime_profile, RuntimeProfile
from core.runtime.runtime_path_validator import RuntimePathValidator

class RealitySnapshotService:
    def __init__(self, workspace_root: str = "C:/ProgramasGodMode", profile: Optional[RuntimeProfile] = None):
        self.workspace_root = Path(workspace_root)
        self.registry = EcosystemRegistry()
        self.runtime_root = Path("C:/DevopGodMode")
        # Base dir for provider discovery
        self.base_dir = Path(__file__).parent.parent.parent
        self.profile = profile or detect_runtime_profile()
        self.path_validator = RuntimePathValidator()
        self._last_snapshot_at = 0.0
        self._last_snapshot: Dict[str, Any] = {}

    def _interval_for_mode(self, mode: str) -> int:
        if mode == "active":
            return self.profile.active_snapshot_interval
        if mode == "degraded":
            return self.profile.degraded_snapshot_interval
        return self.profile.idle_snapshot_interval

    def snapshot(self, mode: str = "idle", force: bool = False) -> Dict[str, Any]:
        """
        Collects actual observed state.
        """
        now = time.time()
        interval = self._interval_for_mode(mode)
        if not force and self._last_snapshot and now - self._last_snapshot_at < interval:
            dgm_logger.debug(f"RealitySnapshotService: Reusing cached {mode} snapshot.")
            return self._last_snapshot

        dgm_logger.debug("RealitySnapshotService: Capturing snapshot...")
        start_time = time.time()

        try:
            snapshot_data = {
                "timestamp": datetime.now().isoformat(),
                "machine": platform.node(),
                "runtime": self._get_runtime_folders(),
                "providers": self._get_providers_status(),
                "repos": self._get_cloned_repos(),
                "agents": self._get_agent_status(),
                "workspaces": self._get_workspace_state(),
                "processes": self._get_running_processes(),
                "memory": self._get_memory_folders(),
                "canonical_paths": self._validate_canonical_paths(),
                "queue": self._get_queue_status()
            }

            elapsed = time.time() - start_time
            self._last_snapshot = snapshot_data
            self._last_snapshot_at = now
            dgm_logger.debug(f"RealitySnapshotService: Snapshot captured in {elapsed:.2f}s")
            return snapshot_data
        except Exception as e:
            dgm_logger.error(f"RealitySnapshotService: Failed to capture snapshot: {e}")
            return {}

    def snapshot_summary(self, data: Optional[Dict[str, Any]] = None, mode: str = "idle") -> Dict[str, Any]:
        data = data or self.snapshot(mode=mode)
        if not data:
            return {"status": "error"}

        runtime_paths_valid = self.path_validator.is_valid(data.get("runtime", {}))
        return {
            "timestamp": data.get("timestamp"),
            "total_repos": len(data.get("repos", [])),
            "total_processes": len(data.get("processes", [])),
            "active_providers": len([p for p in data.get("providers", []) if p.get("status") == "active" or p.get("status") == "ok"]),
            "is_runtime_healthy": runtime_paths_valid,
            "canonical_paths_valid": all(data.get("canonical_paths", {}).values()),
            "queue_health": data.get("queue", {}).get("health", {}),
            "runtime_profile": self.profile.name,
            "low_memory_profile": self.profile.low_memory,
            "system_memory_percent": self.profile.memory_percent
        }

    def _get_runtime_folders(self) -> Dict[str, Any]:
        return self.path_validator.validate(ensure=True)

    def _validate_canonical_paths(self) -> Dict[str, bool]:
        paths = [str(path) for path in RuntimePathValidator.REQUIRED_PATHS]
        results = {}
        for p in paths:
            try:
                results[p] = Path(p).exists()
            except Exception:
                results[p] = False
        return results

    def _get_providers_status(self) -> List[Dict[str, Any]]:
        # Requirement 6: Provider truth
        installed_providers = self._scan_installed_providers()
        registered_providers = provider_registry.list_providers()

        providers_status = []
        all_provider_names = set(installed_providers) | set(registered_providers)

        for name in all_provider_names:
            provider = provider_registry.get_provider(name)
            is_installed = name in installed_providers
            is_loaded = provider is not None

            status = "unknown"
            healthy = False
            available = False
            latency = 0

            if provider:
                if self.profile.lazy_provider_health:
                    status = "deferred"
                else:
                    health_data = provider.check_health()
                    status = health_data.get("status", "unknown")
                    healthy = status == "ok"
                    available = provider.is_available()
                    latency = provider.get_avg_latency()

            providers_status.append({
                "name": name,
                "installed": is_installed,
                "loaded": is_loaded,
                "healthy": healthy,
                "available": available,
                "status": status,
                "latency": latency
            })

        return providers_status

    def _scan_installed_providers(self) -> List[str]:
        providers_dir = self.base_dir / "core" / "providers"
        installed = []
        if providers_dir.exists():
            try:
                for entry in providers_dir.iterdir():
                    if entry.is_dir() and not entry.name.startswith("__"):
                        provider_file = entry / f"{entry.name}_provider.py"
                        if provider_file.exists():
                            installed.append(entry.name)
            except PermissionError:
                pass
        return installed

    def _get_cloned_repos(self) -> List[str]:
        repos = []
        if self.workspace_root.exists():
            try:
                for item in self.workspace_root.iterdir():
                    try:
                        if item.is_dir() and (item / ".git").exists():
                            repos.append(item.name)
                    except PermissionError:
                        continue
            except PermissionError:
                pass

        manual_clones = self.workspace_root / "manual_clones"
        if manual_clones.exists():
            try:
                for item in manual_clones.iterdir():
                    try:
                        if item.is_dir() and (item / ".git").exists():
                            repos.append(f"manual_clones/{item.name}")
                    except PermissionError:
                        continue
            except PermissionError:
                pass
        return repos

    def _get_agent_status(self) -> List[Dict[str, Any]]:
        # This originally used state_store, but it should ideally observe actual process state or separate telemetry
        # For now, we will return an empty list or keep it minimal to avoid circular dependency
        return []

    def _get_workspace_state(self) -> List[str]:
        if not self.workspace_root.exists():
            return []
        try:
            return [item.name for item in self.workspace_root.iterdir() if item.is_dir()]
        except PermissionError:
            return []

    def _get_running_processes(self) -> List[Dict[str, Any]]:
        processes = []
        try:
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    name = proc.info.get('name')
                    if name and ("python" in name.lower() or "dgm" in name.lower()):
                        processes.append(proc.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception:
            pass
        return processes[:50]

    def _get_memory_folders(self) -> Dict[str, Any]:
        memory_root = self.workspace_root / "andreos-memory"
        try:
            exists = memory_root.exists()
            return {
                "path": str(memory_root),
                "exists": exists,
                "is_dir": memory_root.is_dir() if exists else False
            }
        except PermissionError:
            return {"path": str(memory_root), "exists": False, "is_dir": False, "error": "PermissionDenied"}

    def _get_queue_status(self) -> Dict[str, Any]:
        queue = SafeActionQueue()
        return {
            "health": queue.get_health(),
            "queued_count": len(queue.list_queued())
        }
