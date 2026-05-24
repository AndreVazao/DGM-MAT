import time
from typing import Optional, Dict, Any
from core.repository_intelligence.repo_importer import RepoImporter
from core.repository_intelligence.intelligence_engine import IntelligenceEngine
from core.strategy.goal_engine import GoalEngine
from core.observability.logger import dgm_logger
from core.operator.autonomous_operator import AutonomousOperator

class LiveKernel:
    """
    DGM-MAT Live Execution Kernel (v8).
    Orchestrates continuous intelligence cycles and autonomous operator loops.
    """
    def __init__(self, mode: str = "SAFE", interval: int = 60):
        self.mode = mode
        self.interval = interval
        self.importer = RepoImporter()
        self.intel_engine = IntelligenceEngine()
        self.goal_engine = GoalEngine(importer=self.importer)
        self.operator = AutonomousOperator()
        self._running = False

    def run_cycle(self):
        """
        Executes a single intelligence and evolution cycle.
        """
        dgm_logger.info(f"--- KERNEL CYCLE START (Mode: {self.mode}) ---")

        # 1. Autonomous Operator Cycle
        try:
            self.operator.run_cycle()
        except Exception as e:
            dgm_logger.error(f"Kernel: Operator cycle failed: {e}")

        # 2. Scan Ecosystem & Detect Gaps
        try:
            capabilities = self.intel_engine.scan_ecosystem()
            gaps = self.intel_engine.detect_gaps()
            dgm_logger.info(f"Kernel: Current capabilities mapping: {list(capabilities.keys())}")
            dgm_logger.info(f"Kernel: Detected gaps: {[g.value for g in gaps]}")
        except Exception as e:
            dgm_logger.error(f"Kernel: Ecosystem scan failed: {e}")

        # 3. Discover Opportunities
        try:
            opportunities = self.intel_engine.discover_opportunities()
            for opp in opportunities:
                dgm_logger.info(f"Kernel: Opportunity found: {opp['name']} (Score: {opp['score']}) to fill {opp['gap_filled']}")

            # 4. Decision & Execution (if AUTO)
            if self.mode == "AUTO":
                for opp in opportunities:
                    if opp["score"] >= 80:
                        dgm_logger.info(f"Kernel: Auto-importing {opp['name']}...")
                        self.importer.import_repo(opp["url"], category_override=opp["role"])
        except Exception as e:
            dgm_logger.error(f"Kernel: Opportunity discovery failed: {e}")

        dgm_logger.info("--- KERNEL CYCLE COMPLETE ---")

    def start(self):
        """
        Starts the continuous execution loop.
        """
        self._running = True
        self.operator.start()
        dgm_logger.info(f"Live Kernel started in {self.mode} mode.")
        try:
            while self._running:
                self.run_cycle()
                time.sleep(self.interval)
        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        self._running = False
        self.operator.stop()
        dgm_logger.info("Live Kernel stopping...")
