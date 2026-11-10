from dataclasses import dataclass
from threading import Lock

from core.observability.logger import dgm_logger

try:
    import psutil
except ImportError:
    psutil = None


@dataclass(frozen=True)
class RuntimeProfile:
    name: str
    low_memory: bool
    total_ram_gb: float
    memory_percent: float
    idle_snapshot_interval: int
    active_snapshot_interval: int
    degraded_snapshot_interval: int
    governance_monitor_interval: int
    enable_startup_provider_scan: bool
    enable_startup_autonomy_scan: bool
    startup_autonomy_delay: int
    lazy_load_knowledge: bool
    lazy_provider_health: bool
    memory_degradation_threshold: float


_profile_lock = Lock()
_profile: RuntimeProfile | None = None


def detect_runtime_profile() -> RuntimeProfile:
    global _profile
    with _profile_lock:
        if _profile is None:
            _profile = _build_runtime_profile()
        return _profile


def _build_runtime_profile() -> RuntimeProfile:
    total_ram_gb = 0.0
    memory_percent = 0.0

    if psutil:
        vm = psutil.virtual_memory()
        total_ram_gb = round(vm.total / (1024 ** 3), 2)
        memory_percent = float(vm.percent)

    low_memory = bool(total_ram_gb and total_ram_gb < 4.0)

    if low_memory:
        dgm_logger.warning(
            f"LOW_MEMORY_HARDWARE_DETECTED_NO_TASK_RESTRICTIONS: total_ram={total_ram_gb}GB "
            f"memory={memory_percent:.1f}%; tasks remain enabled"
        )

    # Hardware size is retained as diagnostic metadata only. It must not
    # disable engines, defer provider/autonomy scans, or reduce task capability.
    return RuntimeProfile(
        name="low_memory" if low_memory else "standard",
        low_memory=low_memory,
        total_ram_gb=total_ram_gb,
        memory_percent=memory_percent,
        idle_snapshot_interval=30,
        active_snapshot_interval=5,
        degraded_snapshot_interval=60,
        governance_monitor_interval=2,
        enable_startup_provider_scan=True,
        enable_startup_autonomy_scan=True,
        startup_autonomy_delay=10,
        lazy_load_knowledge=False,
        lazy_provider_health=False,
        memory_degradation_threshold=85.0,
    )
