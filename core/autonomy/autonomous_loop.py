import time
import json
import signal
from typing import List, Dict, Any
from datetime import datetime, time as dt_time
from pathlib import Path

from core.observability.logger import dgm_logger
from core.autonomy.scheduler.scheduler_engine import SchedulerEngine
from core.repository_cognition.repo_scanner import CognitiveRepoScanner
from core.autonomy.models import AutonomousTask

class AutonomousLoop:
    def __init__(self, config_path: str = "config/autonomous_runtime.json"):
        self.config = self._load_config(config_path)
        self.scheduler = SchedulerEngine()
        self.repo_scanner = CognitiveRepoScanner()
        self._running = False

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
                self.run_cycle()
                time.sleep(self.config.get("loop_interval", 60))
        except Exception as e:
            dgm_logger.error(f"AutonomousLoop: Loop crashed: {e}")
        finally:
            self.stop()

    def stop(self): self._running = False

    def run_cycle(self):
        task = AutonomousTask(
            task_id="scan_001",
            title="Scan Repository",
            description="Initial system scan",
            priority=10,
            assigned_agent="RepoAgent",
            status="PENDING",
            origin="loop"
        )
        self.scheduler.schedule_task(task)

