from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any

@dataclass
class BootstrapContext:
    runtime_state: str = "initializing"
    start_time: datetime = field(default_factory=datetime.now)
    initialized_modules: List[str] = field(default_factory=list)
    failed_modules: List[str] = field(default_factory=list)
    degraded_modules: List[str] = field(default_factory=list)
    startup_timing: Dict[str, float] = field(default_factory=dict)
    dependency_graph: Dict[str, List[str]] = field(default_factory=dict)
    environment_metadata: Dict[str, Any] = field(default_factory=dict)
    runtime_profile: str = "FULL"
    node_role: str = "DESKTOP_BRAIN"

    def mark_module_success(self, module_name: str, duration: float):
        self.initialized_modules.append(module_name)
        self.startup_timing[module_name] = duration

    def mark_module_failed(self, module_name: str, duration: float):
        self.failed_modules.append(module_name)
        self.startup_timing[module_name] = duration

    def mark_module_degraded(self, module_name: str, duration: float):
        self.degraded_modules.append(module_name)
        self.startup_timing[module_name] = duration
