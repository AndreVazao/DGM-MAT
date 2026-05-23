import time
from typing import Dict, Any
from core.recovery.health_monitor import HealthMonitor
from core.recovery.crash_classifier import CrashClassifier
from core.recovery.isolation_engine import IsolationEngine
from core.recovery.runtime_recovery import RuntimeRecovery
from core.recovery.provider_recovery import ProviderRecovery
from core.recovery.repair_chain import RepairChain
from core.recovery.recovery_memory import RecoveryMemory
from core.observability.logger import dgm_logger

MAX_RECOVERY_RETRIES = 3
RECOVERY_COOLDOWN_SECONDS = 30

class RecoveryEngine:
    def __init__(self):
        self.health_monitor = HealthMonitor()
        self.crash_classifier = CrashClassifier()
        self.isolation_engine = IsolationEngine()
        self.runtime_recovery = RuntimeRecovery()
        self.provider_recovery = ProviderRecovery()
        self.memory = RecoveryMemory()

        self.retry_counts: Dict[str, int] = {}
        self.last_recovery_time: Dict[str, float] = {}

    def handle_crash(self, error_data: dict):
        classification = self.crash_classifier.classify(error_data)
        if not classification:
            return False

        crash_type = classification['type']
        current_time = time.time()

        # 1. Cooldown Check
        last_time = self.last_recovery_time.get(crash_type, 0)
        if current_time - last_time < RECOVERY_COOLDOWN_SECONDS:
            dgm_logger.warning(f"RecoveryEngine: Cooldown active for {crash_type}. Skipping.")
            return False

        # 2. Retry Cap Check
        count = self.retry_counts.get(crash_type, 0)
        if count >= MAX_RECOVERY_RETRIES:
            dgm_logger.critical(f"RecoveryEngine: Max retries exceeded for {crash_type}. Entering degraded mode.")
            return False

        dgm_logger.critical(f"RECOVERY ENGINE: Handling {crash_type} (Attempt {count + 1})...")

        self.retry_counts[crash_type] = count + 1
        self.last_recovery_time[crash_type] = current_time

        chain = RepairChain()
        # Isolate the chain execution
        success = self.isolation_engine.execute_isolated(
            f"recovery_{crash_type}",
            self._execute_chain,
            crash_type
        )

        status = "success" if success else "failed"
        self.memory.record_recovery(crash_type, status)

        if success:
            dgm_logger.info(f"RecoveryEngine: Successfully recovered from {crash_type}")
            self.retry_counts[crash_type] = 0 # Reset on success

        return success

    def _execute_chain(self, crash_type: str) -> bool:
        chain = RepairChain()
        if crash_type == "runtime_crash":
            chain.add_step(self.runtime_recovery.recover)
        elif crash_type == "provider_crash":
            chain.add_step(lambda: self.provider_recovery.recover_provider("default"))
        elif crash_type == "websocket_disconnect":
            # Add specific steps if needed
            chain.add_step(self.runtime_recovery.recover)

        return chain.execute()
