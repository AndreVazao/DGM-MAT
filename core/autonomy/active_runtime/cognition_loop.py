import asyncio
import time
import json
from typing import Dict, Any, List
from datetime import datetime, time as dt_time
from pathlib import Path
from core.observability.logger import dgm_logger
from core.storage.storage_manager import storage_manager
from core.autonomy.active_runtime.autonomy_cycle import AutonomyCycle
from core.autonomy.active_runtime.strategic_planner import StrategicPlanner
from core.autonomy.active_runtime.objective_engine import ObjectiveEngine
from core.autonomy.active_runtime.execution_director import ExecutionDirector
from core.autonomy.active_runtime.learning_loop import LearningLoop
from core.autonomy.scheduler.scheduler_engine import SchedulerEngine
from core.repository_cognition.repo_scanner import CognitiveRepoScanner

class CognitionLoop:
    def __init__(self, config_path: str = "config/autonomous_runtime.json"):
        self.running = False
        self.cycle_count = 0
        self.storage_path = storage_manager.get_path("cognition") / "autonomy_cycles"
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.config = self._load_config(config_path)
        self.planner = StrategicPlanner()
        self.objective_engine = ObjectiveEngine()
        self.director = ExecutionDirector()
        self.learning_loop = LearningLoop()
        self.scheduler = SchedulerEngine()
        self.repo_scanner = CognitiveRepoScanner()

    def _load_config(self, path: str) -> Dict[str, Any]:
        p = Path(path)
        if not p.exists():
            return {"loop_interval": 60, "night_cycle_start": "02:00", "night_cycle_duration_hours": 4}
        with open(p, "r") as f:
            return json.load(f)

    async def start(self):
        self.running = True
        dgm_logger.info("CognitionLoop: Starting unified autonomous daemon loop.")
        while self.running:
            try:
                if self._is_night_cycle(): await self.run_night_cycle()
                else: await self.run_cycle()
                await asyncio.sleep(self.config.get("loop_interval", 60))
            except Exception as e:
                dgm_logger.error(f"CognitionLoop: Daemon loop error: {e}")
                await asyncio.sleep(30)

    def _is_night_cycle(self) -> bool:
        now = datetime.now().time()
        start_str = self.config.get("night_cycle_start", "02:00")
        start_t = dt_time.fromisoformat(start_str)
        duration = self.config.get("night_cycle_duration_hours", 4)
        end_hour = (start_t.hour + duration) % 24
        if start_t.hour < end_hour: return start_t <= now <= dt_time(hour=end_hour)
        else: return now >= start_t or now <= dt_time(hour=end_hour)

    async def run_cycle(self):
        cycle = AutonomyCycle()
        self.cycle_count += 1
        dgm_logger.info(f"CognitionLoop: Starting cycle {self.cycle_count} ({cycle.cycle_id})")

        try:
            # 1. OBSERVE
            state = self.repo_scanner.scan()
            cycle.metadata["observation"] = {"repo_files": len(state)}

            # 2. ANALYZE
            analysis = self.planner.analyze_repository()
            cycle.metadata["analysis"] = analysis

            # 3. PLAN
            objectives = self.objective_engine.generate_objectives(analysis)
            cycle.objectives = objectives

            # 4. PRIORITIZE
            # (In real logic, we'd sort objectives by priority here)
            prioritized_objectives = sorted(objectives, key=lambda x: x.get('priority', 0), reverse=True)

            # 5. EXECUTE
            task_ids = self.director.assign_tasks(prioritized_objectives)
            cycle.results = [{"task_id": tid, "status": "PENDING"} for tid in task_ids]

            # 6. VALIDATE
            # (Wait for tasks or check immediate validity)
            validation_results = self.director.validate_execution(task_ids)
            cycle.metadata["validation"] = validation_results

            # 7. REFLECT
            reflection = self.learning_loop.reflect_on_cycle(cycle.to_dict())
            cycle.metadata["reflection"] = reflection

            # 8. STORE MEMORY
            self.learning_loop.store_experience(cycle.to_dict())

            # 9. SELF-IMPROVE
            adjustments = self.learning_loop.generate_self_improvements(reflection)
            cycle.metadata["self_improvement"] = adjustments

            # 10. REPEAT (Handled by the main while loop)
            dgm_logger.info(f"CognitionLoop: Cycle {cycle.cycle_id} completed successfully.")

        except Exception as e:
            dgm_logger.error(f"CognitionLoop: Cycle failed during execution: {e}")
            cycle.status = "FAILED"
            cycle.metadata["error"] = str(e)
        finally:
            cycle.complete()
            cycle.persist(self.storage_path)

    async def run_night_cycle(self):
        dgm_logger.info("CognitionLoop: Running night cycle (Consolidation).")
        await asyncio.sleep(0.1)

    def stop(self):
        self.running = False
