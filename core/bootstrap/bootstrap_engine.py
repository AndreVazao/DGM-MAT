import time
import json
import os
from pathlib import Path
from datetime import datetime
from core.observability.logger import dgm_logger
from core.bootstrap.bootstrap_context import BootstrapContext
from core.bootstrap.bootstrap_sequence import BootstrapPhase, BOOTSTRAP_ORDER
from core.bootstrap.environment_detector import detect_environment, assign_node_role
from core.bootstrap.bootstrap_storage import initialize_storage_subsystem
from core.bootstrap.dependency_loader import DependencyLoader

class BootstrapEngine:
    """
    Minimalist Bootstrap Engine.
    Phase 42.1: Handles environment validation and canonical path initialization.
    """
    def __init__(self, profile: str = "FULL"):
        self.context = BootstrapContext(runtime_profile=profile)
        self.handlers = {
            BootstrapPhase.VALIDATE_ENVIRONMENT: self._validate_environment,
            BootstrapPhase.INITIALIZE_STORAGE: self._initialize_storage,
            BootstrapPhase.VALIDATE_RUNTIME_PATHS: self._validate_runtime_paths,
            BootstrapPhase.LOAD_ECOSYSTEM_REGISTRY: self._load_ecosystem,
            BootstrapPhase.INITIALIZE_GOVERNANCE: self._prepare_governance,
            BootstrapPhase.INITIALIZE_MEMORY_SYSTEMS: self._prepare_memory,
            BootstrapPhase.INITIALIZE_PROVIDERS: self._prepare_providers,
            BootstrapPhase.INITIALIZE_FEDERATION: self._prepare_federation,
            BootstrapPhase.INITIALIZE_RUNTIME_KERNEL: self._prepare_kernel,
            BootstrapPhase.INITIALIZE_REALTIME_LAYER: self._prepare_realtime,
            BootstrapPhase.INITIALIZE_COCKPIT_BRIDGE: self._prepare_cockpit_bridge,
            BootstrapPhase.VALIDATE_HEALTH: self._validate_health,
            BootstrapPhase.EXPOSE_RUNTIME_STATE: self._expose_state,
        }

    def prepare(self):
        dgm_logger.info(f"BootstrapEngine: Preparing system with profile {self.context.runtime_profile}")
        total_start = time.time()
        for phase in BOOTSTRAP_ORDER:
            phase_start = time.time()
            try:
                dgm_logger.info(f"BootstrapEngine: Processing phase {phase.name}...")
                handler = self.handlers.get(phase)
                if handler:
                    handler()
                duration = time.time() - phase_start
                self.context.mark_module_success(phase.name, duration)
            except Exception as e:
                duration = time.time() - phase_start
                dgm_logger.error(f"BootstrapEngine: Phase {phase.name} failed: {e}")
                self.context.mark_module_failed(phase.name, duration)
                if self._is_critical_phase(phase):
                    dgm_logger.critical(f"BootstrapEngine: Critical phase {phase.name} failed. Preparation aborted.")
                    self.context.runtime_state = "failed"
                    self._expose_state()
                    return self.context
                else:
                    self.context.mark_module_degraded(phase.name, duration)

        self.context.runtime_state = "prepared"
        self._expose_state()
        return self.context

    def _is_critical_phase(self, phase):
        critical_phases = [
            BootstrapPhase.VALIDATE_ENVIRONMENT,
            BootstrapPhase.INITIALIZE_STORAGE,
            BootstrapPhase.INITIALIZE_GOVERNANCE,
        ]
        return phase in critical_phases

    def _validate_environment(self):
        self.context.environment_metadata = detect_environment()
        self.context.node_role = assign_node_role(self.context.environment_metadata)

        # Requirement 1: Canonical path validation
        if os.name == 'nt':
            paths = ["C:/DevopGodMode", "C:/ProgramasGodMode", "C:/ProgramasGodMode/andreos-memory"]
            for p in paths:
                try:
                    Path(p).mkdir(parents=True, exist_ok=True)
                    dgm_logger.info(f"BootstrapEngine: Validated path {p}")
                except Exception as e:
                    dgm_logger.warning(f"BootstrapEngine: Could not validate path {p}: {e}")

    def _initialize_storage(self):
        initialize_storage_subsystem()

    def _validate_runtime_paths(self):
        from core.storage.storage_manager import storage_manager
        if not storage_manager.base_path.exists():
            storage_manager._ensure_structure()

    def _load_ecosystem(self): pass

    def _prepare_governance(self):
        DependencyLoader.validate_dependency("core.governance.governance_engine", critical=True)

    def _prepare_memory(self):
        DependencyLoader.validate_dependency("core.memory.memory_manager")

    def _prepare_providers(self):
        DependencyLoader.validate_dependency("core.providers.provider_registry")

    def _prepare_federation(self):
        DependencyLoader.validate_dependency("core.federation.federation_engine")

    def _prepare_kernel(self):
        DependencyLoader.validate_dependency("core.kernel.cognitive_kernel")

    def _prepare_realtime(self):
        DependencyLoader.validate_dependency("core.realtime.websocket_manager")

    def _prepare_cockpit_bridge(self):
        if self.context.runtime_profile != "HEADLESS":
            DependencyLoader.validate_dependency("PySide6")

    def _validate_health(self): pass

    def _expose_state(self):
        from core.storage.storage_manager import storage_manager
        health_file = storage_manager.get_path("temp", "startup_health.json")
        health_data = {
            "status": self.context.runtime_state,
            "profile": self.context.runtime_profile,
            "role": self.context.node_role,
            "initialized": self.context.initialized_modules,
            "failed": self.context.failed_modules,
            "degraded": self.context.degraded_modules,
            "environment": self.context.environment_metadata,
            "timestamp": datetime.now().isoformat()
        }
        with open(health_file, "w") as f:
            json.dump(health_data, f, indent=4)
