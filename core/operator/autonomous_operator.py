from typing import Dict, Any, List
from core.observability.logger import dgm_logger
from core.operator.autonomous_scheduler import AutonomousScheduler
from core.operator.task_daemon import TaskDaemon

class AutonomousOperator:
    """
    Main entry point for the autonomous operator.
    Orchestrates background tasks, scheduling, and self-improvement loops.
    """
    def __init__(self):
        self.scheduler = AutonomousScheduler()
        self.daemon = TaskDaemon()
        self._running = False

    def run_cycle(self):
        dgm_logger.info("Autonomous Operator Cycle Start")
        # 1. Trigger Scheduled Tasks
        self.scheduler.run_pending()
        # 2. Process Task Queue
        self.daemon.process_queue()
        dgm_logger.info("Autonomous Operator Cycle End")

    def start(self):
        self._running = True
        dgm_logger.info("Autonomous Operator Started.")

    def stop(self):
        self._running = False
        dgm_logger.info("Autonomous Operator Stopped.")
