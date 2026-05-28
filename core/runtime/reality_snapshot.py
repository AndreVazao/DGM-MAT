import os
import psutil
import time
import platform
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime
from core.observability.logger import dgm_logger
from core.ecosystem.ecosystem_registry import EcosystemRegistry
from core.runtime.safe_action_queue import SafeActionQueue
from core.provider_sync.provider_registry import provider_registry

class RealitySnapshotService:
    def __init__(self, workspace_root: str = "C:/ProgramasGodMode"):
        self.workspace_root = Path(workspace_root)
        self.registry = EcosystemRegistry()
        self.runtime_root = Path("C:/DevopGodMode")
        # Base dir for provider discovery
        self.base_dir = Path(__file__).parent.parent.parent

    def snapshot(self) -> Dict[str, Any]:
        """
        Collects actual observed state.
        """
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
            dgm_logger.debug(f"RealitySnapshotService: Snapshot captured in {elapsed:.2f}s")
            return snapshot_data
        except Exception as e:
            dgm_logger.error(f"RealitySnapshotService: Failed to capture snapshot: {e}")
            return {}

    def snapshot_summary(self) -> Dict[str, Any]:
        data = self.snapshot()
        if not data:
            return {"status": "error"}

        return {
            "timestamp": data.get("timestamp"),
            "total_repos": len(data.get("repos", [])),
            "total_processes": len(data.get("processes", [])),
            "active_providers": len([p for p in data.get("providers", []) if p.get("status") == "active" or p.get("status") == "ok"]),
            "is_runtime_healthy": all(v.get("exists") for v in data.get("runtime", {}).values()),
            "canonical_paths_valid": all(data.get("canonical_paths", {}).values()),
            "queue_health": data.get("queue", {}).get("health", {})
        }

    def _get_runtime_folders(self) -> Dict[str, Any]:
        folders = ["runtime", "storage", "config", "logs"]
        result = {}
        for folder in folders:
            path = self.runtime_root / folder
            try:
                exists = path.exists()
                result[folder] = {
                    "path": str(path),
                    "exists": exists,
                    "is_dir": path.is_dir() if exists else False
                }
            except PermissionError:
                result[folder] = {"path": str(path), "exists": False, "is_dir": False, "error": "PermissionDenied"}
        return result

    def _validate_canonical_paths(self) -> Dict[str, bool]:
        paths = ["C:/DevopGodMode", "C:/ProgramasGodMode", "C:/ProgramasGodMode/andreos-memory"]
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
