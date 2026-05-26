import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from core.storage.storage_manager import storage_manager
from core.observability.logger import dgm_logger

class ExecutionQuota(BaseModel):
    autonomous_limit: int = 50 # Max autonomous operations per hour
    provider_token_limit: int = 1000000 # Max tokens per day
    modification_budget: int = 5 # Max files modified per session
    current_autonomous_count: int = 0
    current_token_count: int = 0
    current_modification_count: int = 0
    last_reset: datetime = Field(default_factory=datetime.now)
    # Phase 37 Extensions
    max_simultaneous_tasks: int = 10
    degraded_mode_threshold: float = 0.8 # 80% failure rate triggers degraded mode
    cooldown_seconds: int = 60

class ExecutionGovernor:
    """
    Prevents runaway execution, limits autonomous scope, blocks dangerous
    modifications, and enforces execution budgets.
    """
    def __init__(self):
        self.storage = storage_manager
        self.governance_domain = "governance"
        self.quota_filename = "execution_quotas.json"
        self.quota = self._load_quota()
        self.dangerous_patterns = ["rm -rf /", "mkfs", "> /dev/sda", "chmod 777 /"]
        self.active_tasks_count = 0

    def _load_quota(self) -> ExecutionQuota:
        content = self.storage.read_data(self.governance_domain, self.quota_filename)
        if content:
            try:
                data = json.loads(content)
                return ExecutionQuota(**data)
            except Exception as e:
                dgm_logger.error(f"ExecutionGovernor: Failed to load quota: {e}")
        return ExecutionQuota()

    def _save_quota(self):
        self.storage.save_data(self.governance_domain, self.quota_filename, self.quota.model_dump_json(indent=2))

    def _reset_if_needed(self):
        now = datetime.now()
        if now - self.quota.last_reset > timedelta(hours=1):
            self.quota.current_autonomous_count = 0
            self.quota.last_reset = now
        # Token reset daily (simplified)
        if now.date() != self.quota.last_reset.date():
             self.quota.current_token_count = 0
        self._save_quota()

    def authorize_execution(self, scope: str, description: str, metadata: Dict[str, Any] = None) -> bool:
        """Checks if an autonomous operation is within limits and safe."""
        self._reset_if_needed()

        # 1. Budget Checks
        if self.quota.current_autonomous_count >= self.quota.autonomous_limit:
            dgm_logger.warning("ExecutionGovernor: Autonomous operation limit reached.")
            return False

        if self.active_tasks_count >= self.quota.max_simultaneous_tasks:
            dgm_logger.warning("ExecutionGovernor: Max simultaneous tasks reached.")
            return False

        # 2. Safety Checks
        if any(p in description.lower() for p in self.dangerous_patterns):
            dgm_logger.error(f"ExecutionGovernor: Dangerous pattern detected in operation: {description}")
            return False

        # 3. Scope Checks
        if "core/" in scope and metadata.get("execution_mode") != "SYSTEM":
             dgm_logger.warning(f"ExecutionGovernor: Blocked non-system modification to core: {scope}")
             return False

        # Increment count
        self.quota.current_autonomous_count += 1
        self._save_quota()
        dgm_logger.info(f"ExecutionGovernor: Authorized execution for {scope}")
        return True

    def report_task_start(self):
        self.active_tasks_count += 1

    def report_task_end(self):
        self.active_tasks_count = max(0, self.active_tasks_count - 1)

    def report_token_usage(self, count: int):
        self.quota.current_token_count += count
        self._save_quota()

    def quarantine_module(self, module_id: str, reason: str):
        """Places a failing or unstable module in quarantine."""
        dgm_logger.warning(f"ExecutionGovernor: Quarantining module {module_id}. Reason: {reason}")
        # In a real scenario, this would update a registry or block the module in the event bus.
        quarantine_data = self.storage.read_data(self.governance_domain, "quarantine.json")
        q_list = json.loads(quarantine_data) if quarantine_data else {}
        q_list[module_id] = {"reason": reason, "timestamp": datetime.now().isoformat()}
        self.storage.save_data(self.governance_domain, "quarantine.json", json.dumps(q_list, indent=2))

    def is_quarantined(self, module_id: str) -> bool:
        quarantine_data = self.storage.read_data(self.governance_domain, "quarantine.json")
        if not quarantine_data:
            return False
        q_list = json.loads(quarantine_data)
        return module_id in q_list

# Singleton instance
execution_governor = ExecutionGovernor()
