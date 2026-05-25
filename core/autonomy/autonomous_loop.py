import time
import json
from typing import List, Dict, Any
from datetime import datetime, time as dt_time
from pathlib import Path

from core.observability.logger import dgm_logger
from core.autonomy.task_generator import TaskGenerator
from core.autonomy.priority_engine import PriorityEngine
from core.autonomy.safe_autonomous_executor import SafeAutonomousExecutor
from core.autonomy.repo_analysis_pipeline import RepoAnalysisPipeline
from core.memory.consolidation_engine import MemoryConsolidationEngine
from core.cognition.cognitive_analysis_engine import cognitive_engine
from core.autonomy.self_improvement_planner import improvement_planner
from core.repository_intelligence.repo_federation import repo_federation

class AutonomousLoop:
    """
    The perpetual heart of DGM-MAT's autonomous operations.
    Extended with cognitive analysis and strategic planning cycles.
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
                if self._is_night_cycle():
                    self.run_night_cycle()
                else:
                    self.run_cycle()

                interval = self.config.get("loop_interval", 60)
                dgm_logger.info(f"AutonomousLoop: Sleeping for {interval}s...")
                time.sleep(interval)
        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        self._running = False
        dgm_logger.info("AutonomousLoop: Stopping...")

    def _is_night_cycle(self) -> bool:
        """Determines if the system is currently in a scheduled night cycle."""
        now = datetime.now().time()
        start_str = self.config.get("night_cycle_start", "02:00")
        start_t = dt_time.fromisoformat(start_str)

        duration = self.config.get("night_cycle_duration_hours", 4)
        # Simplified check
        return start_t <= now <= dt_time(hour=(start_t.hour + duration) % 24)

    def run_cycle(self):
        """Standard tactical autonomous cycle."""
        dgm_logger.info(f"--- AUTONOMOUS CYCLE START: {datetime.now().isoformat()} ---")
        self._update_state("TACTICAL_CYCLE")

        # Placeholder for tactical task execution
        # 1. scan_state -> 2. collect_inputs -> 3. analyze -> 4. prioritize -> 5. plan -> 6. execute -> etc.

        dgm_logger.info("--- AUTONOMOUS CYCLE COMPLETE ---")
        self._update_state("SLEEPING")

    def run_night_cycle(self):
        """Deep analysis and strategic planning cycle (Night Cycle)."""
        dgm_logger.info(f"--- NIGHT CYCLE START: {datetime.now().isoformat()} ---")
        self._update_state("NIGHT_CYCLE")

        # 1. Deep Repo Analysis
        repo_federation.detect_overlaps()
        repo_federation.rank_usefulness()

        # 2. Memory Consolidation
        self.consolidation_engine.consolidate()

        # 3. Strategic Planning
        # In a real scenario, we would iterate through repos
        # weaknesses = improvement_planner.evaluate_weaknesses(cognitive_reports)
        # improvement_planner.generate_strategic_goals(weaknesses)

        dgm_logger.info("--- NIGHT CYCLE COMPLETE ---")
        self._update_state("SLEEPING")

    def _update_state(self, status: str):
        state = {
            "last_heartbeat": datetime.now().isoformat(),
            "status": status,
            "current_mode": self.config.get("execution_mode"),
            "config": self.config
        }
        with open(self.state_file, "w") as f:
            json.dump(state, f, indent=2)
