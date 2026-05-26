import asyncio
import time
from typing import Dict, Any
from pathlib import Path
from core.observability.logger import dgm_logger
from core.storage.storage_manager import storage_manager
from core.autonomy.active_runtime.autonomy_cycle import AutonomyCycle
from core.autonomy.active_runtime.strategic_planner import StrategicPlanner
from core.autonomy.active_runtime.objective_engine import ObjectiveEngine
from core.autonomy.active_runtime.execution_director import ExecutionDirector
from core.autonomy.active_runtime.learning_loop import LearningLoop

class CognitionLoop:
    def __init__(self):
        self.running = False
        self.cycle_count = 0
        self.storage_path = storage_manager.get_path("cognition") / "autonomy_cycles"
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.cooldown = 60 # Default cooldown

        self.planner = StrategicPlanner()
        self.objective_engine = ObjectiveEngine()
        self.director = ExecutionDirector()
        self.learning_loop = LearningLoop()

    async def start(self):
        self.running = True
        dgm_logger.info("CognitionLoop: Starting active autonomous loop.")
        while self.running:
            try:
                await self.run_cycle()
                await asyncio.sleep(self.cooldown)
            except Exception as e:
                dgm_logger.error(f"CognitionLoop: Cycle failed: {e}")
                await asyncio.sleep(30) # Extended cooldown on error

    async def run_cycle(self):
        cycle = AutonomyCycle()
        self.cycle_count += 1
        dgm_logger.info(f"CognitionLoop: Starting cycle {self.cycle_count} ({cycle.cycle_id})")

        # 1. Analyze state
        analysis = self.planner.analyze_repository()
        cycle.metadata["analysis"] = analysis

        # 2. Generate objectives
        objectives = self.objective_engine.generate_objectives(analysis)
        cycle.objectives = objectives

        # 3. Direct execution
        task_ids = self.director.assign_tasks(objectives)
        cycle.results = [{"task_id": tid, "status": "PENDING"} for tid in task_ids]

        # 4. Learning loop (Feedback processing)
        # In a real loop, we'd wait for some results or process past results
        self.learning_loop.process_feedback(cycle.results)

        cycle.complete()
        cycle.persist(self.storage_path)
        dgm_logger.info(f"CognitionLoop: Cycle {cycle.cycle_id} completed and persisted.")

    def stop(self):
        self.running = False
