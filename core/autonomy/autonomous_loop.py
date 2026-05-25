import time
import json
import signal
from typing import List, Dict, Any
from datetime import datetime, time as dt_time
from pathlib import Path

from core.observability.logger import dgm_logger
from core.autonomy.scheduler.scheduler_engine import SchedulerEngine
from core.repository_cognition.repo_scanner import CognitiveRepoScanner
from core.knowledge_graph.memory_consolidator import KnowledgeConsolidator
from core.knowledge_graph.graph_store import GraphStore

class AutonomousLoop:
    def __init__(self, config_path: str = "config/autonomous_runtime.json"):
        self.config = self._load_config(config_path)
        self.scheduler = SchedulerEngine()
        self.repo_scanner = CognitiveRepoScanner()
        self.graph_store = GraphStore()
        self.consolidator = KnowledgeConsolidator(self.graph_store)
        self._running = False
        self.state_file = Path(".runtime/autonomy_state.json")

    def _load_config(self, path: str) -> Dict[str, Any]:
        p = Path(path)
        if not p.exists():
            return {"loop_interval": 60, "night_cycle_start": "02:00", "night_cycle_duration_hours": 4}
        with open(p, "r") as f:
            return json.load(f)

    def start(self):
        self._running = True
        try:
            while self._running:
                if self._is_night_cycle(): self.run_night_cycle()
                else: self.run_cycle()
                time.sleep(self.config.get("loop_interval", 60))
        except Exception as e:
            dgm_logger.error(f"AutonomousLoop: Loop crashed: {e}")
        finally:
            self.stop()

    def stop(self): self._running = False

    def _is_night_cycle(self) -> bool:
        now = datetime.now().time()
        start_str = self.config.get("night_cycle_start", "02:00")
        start_t = dt_time.fromisoformat(start_str)
        duration = self.config.get("night_cycle_duration_hours", 4)
        return start_t <= now <= dt_time(hour=(start_t.hour + duration) % 24)

    def run_cycle(self):
        self.scheduler.schedule_task("scan", "scan", {"path": "."})

    def run_night_cycle(self):
        self.consolidator.consolidate_all()
