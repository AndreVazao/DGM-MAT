import json
import os
import threading
import concurrent.futures
from shared.models.event import Event
from shared.enums.event_priority import EventPriority
from core.observability.logger import dgm_logger
from core.governance.runtime_limits import RuntimeLimits
from core.governance.event_governor import EventGovernor
from core.governance.loop_detector import LoopDetector
from core.governance.recursion_guard import RecursionGuard
from core.governance.resource_monitor import ResourceMonitor
from core.governance.memory_controller import MemoryController
from core.governance.execution_throttler import ExecutionThrottler
from core.governance.queue_balancer import QueueBalancer
from core.governance.deadlock_detector import DeadlockDetector
from core.governance.storm_protection import StormProtection
from core.governance.provider_rate_control import ProviderRateControl
from core.governance.workload_scheduler import WorkloadScheduler
from core.governance.degradation_controller import DegradationController
from core.governance.self_modification_guard import SelfModificationGuard
from core.runtime.runtime_profile import detect_runtime_profile

class GovernanceEngine:
    def __init__(self, config_path: str = "config/runtime_limits.json"):
        self.limits = self._load_limits(config_path)
        self.profile = detect_runtime_profile()
        if self.profile.low_memory:
            self.limits.memory_degradation_threshold = self.profile.memory_degradation_threshold
        self.lock = threading.Lock()

        # Initialize components
        self.event_governor = EventGovernor(self.limits)
        self.loop_detector = LoopDetector()
        self.recursion_guard = RecursionGuard(self.limits.max_recursion_depth)
        self.resource_monitor = ResourceMonitor()
        self.memory_controller = MemoryController(self.limits.memory_degradation_threshold)
        self.throttler = ExecutionThrottler()
        self.balancer = QueueBalancer()
        self.deadlock_detector = DeadlockDetector()
        self.storm_protection = StormProtection(
            self.limits.storm_event_count_threshold,
            self.limits.storm_time_window_seconds
        )
        self.provider_rate_control = ProviderRateControl(self.limits.max_provider_requests_per_min)
        self.workload_scheduler = WorkloadScheduler()
        self.degradation_controller = DegradationController()
        self.modification_guard = SelfModificationGuard()

        self.is_running = True
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=2, thread_name_prefix="governance")

    def _load_limits(self, path: str) -> RuntimeLimits:
        if os.path.exists(path):
            try:
                with open(path, 'r') as f:
                    data = json.load(f)
                return RuntimeLimits(**data)
            except Exception as exc:
                dgm_logger.error(f"GovernanceEngine: Failed to load limits from {path}: {exc}")
        return RuntimeLimits()

    def govern_modification(self, file_path: str) -> bool:
        """Checks if a file modification is allowed by the self-modification guard."""
        return self.modification_guard.is_modification_allowed(file_path)

    def govern_event(self, event: Event) -> bool:
        """Central entry point for event governance. Hardened with timeout and safety."""
        if not self.is_running:
            return True # Fallback to allowed in case of engine failure

        try:
            # Use a future with timeout to prevent governance from blocking the event bus
            future = self.executor.submit(self._run_governance_checks, event)
            return future.result(timeout=0.05) # 50ms max for governance
        except concurrent.futures.TimeoutError:
            dgm_logger.warning(f"GovernanceEngine: Timeout checking event {event.event_type}. Allowing as safety fallback.")
            return True
        except Exception as exc:
            dgm_logger.error(f"GovernanceEngine: Critical failure during checks: {exc}")
            return True # Defensive fallback

    def _run_governance_checks(self, event: Event) -> bool:
        """Internal synchronous check logic."""
        with self.lock:
            # 1. Event Governor (depth & general rate)
            if not self.event_governor.govern(event):
                return False

            # 2. Loop detection
            if self.loop_detector.detect_loop(event):
                return False

            # 3. Storm protection
            if self.storm_protection.check_storm(event.source):
                self.degradation_controller.state.emergency_slowdown = True
                return False

            # 4. Degradation check
            if self.degradation_controller.should_throttle_low_priority() and event.priority == EventPriority.LOW:
                dgm_logger.info(f"GovernanceEngine: Throttling low priority event {event.event_type} due to degradation.")
                return False

        return True

    def start_monitoring(self):
        self.resource_monitor.interval = self.profile.governance_monitor_interval
        self.resource_monitor.start(callback=self._handle_resource_update)

    def _handle_resource_update(self, snapshot):
        try:
            self.memory_controller.check_memory(snapshot)
            self.degradation_controller.update_degradation(
                snapshot.cpu_percent,
                snapshot.memory_percent,
                self.limits.cpu_degradation_threshold,
                self.limits.memory_degradation_threshold
            )
        except Exception as exc:
            dgm_logger.error(f"GovernanceEngine: Resource update failure: {exc}")

    def shutdown(self):
        self.is_running = False
        self.executor.shutdown(wait=False)
