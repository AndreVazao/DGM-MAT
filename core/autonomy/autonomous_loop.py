import time
import json
from typing import List, Dict, Any
from datetime import datetime
from pathlib import Path

from core.observability.logger import dgm_logger
from core.autonomy.task_generator import TaskGenerator
from core.autonomy.priority_engine import PriorityEngine
from core.autonomy.safe_autonomous_executor import SafeAutonomousExecutor
from core.autonomy.repo_analysis_pipeline import RepoAnalysisPipeline
from core.memory.consolidation_engine import MemoryConsolidationEngine

class AutonomousLoop:
    """
    The perpetual heart of DGM-MAT's autonomous operations.
    """
    def __init__(self, config_path: str = "config/autonomous_runtime.json"):
        self.config = self._load_config(config_path)
        self.task_generator = TaskGenerator()
        self.priority_engine = PriorityEngine()
        self.executor = SafeAutonomousExecutor(mode=self.config.get("execution_mode", "SAFE"))
        self.analysis_pipeline = RepoAnalysisPipeline()
        self.consolidation_engine = MemoryConsolidationEngine()
        self._running = False
        self.state_file = Path(".runtime/runtime_state.json")

    def _load_config(self, path: str) -> Dict[str, Any]:
        with open(path, "r") as f:
            return json.load(f)

    def start(self):
        self._running = True
        dgm_logger.info("AutonomousLoop: Starting perpetual cycle...")
        try:
            while self._running:
                self.run_cycle()
                interval = self.config.get("loop_interval", 60)
                dgm_logger.info(f"AutonomousLoop: Sleeping for {interval}s...")
                time.sleep(interval)
        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        self._running = False
        dgm_logger.info("AutonomousLoop: Stopping...")

    def run_cycle(self):
        """The 10-phase cycle."""
        dgm_logger.info(f"--- AUTONOMOUS CYCLE START: {datetime.now().isoformat()} ---")

        # 1. scan_state
        self._update_state("SCANNING")

        # 2. collect_inputs (e.g. TODOs)
        # 3. analyze
        # 4. prioritize
        # 5. plan
        # 6. execute_safe
        # 7. validate
        # 8. persist_memory
        # 9. update_metrics
        # 10. sleep

        dgm_logger.info("--- AUTONOMOUS CYCLE COMPLETE ---")
        self._update_state("SLEEPING")

    def _update_state(self, status: str):
        state = {
            "last_heartbeat": datetime.now().isoformat(),
            "status": status,
            "config": self.config
        }
        with open(self.state_file, "w") as f:
            json.dump(state, f, indent=2)
