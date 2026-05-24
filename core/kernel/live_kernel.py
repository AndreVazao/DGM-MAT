import time
from typing import Optional, Dict, Any
from core.repository_intelligence.repo_importer import RepoImporter
from core.repository_intelligence.intelligence_engine import IntelligenceEngine
from core.strategy.goal_engine import GoalEngine
from core.observability.logger import dgm_logger

class LiveKernel:
    """
    DGM-MAT Live Execution Kernel (v7).
    Orchestrates continuous intelligence cycles and autonomous evolution.
    """
    def __init__(self, mode: str = "SAFE", interval: int = 60):
        self.mode = mode
        self.interval = interval
        self.importer = RepoImporter()
        self.intel_engine = IntelligenceEngine()
        self.goal_engine = GoalEngine(importer=self.importer)
        self._running = False

    def run_cycle(self):
        """
        Executes a single intelligence and evolution cycle.
        """
        dgm_logger.info(f"--- KERNEL CYCLE START (Mode: {self.mode}) ---")

        # 1. Scan Ecosystem & Detect Gaps
        capabilities = self.intel_engine.scan_ecosystem()
        gaps = self.intel_engine.detect_gaps()
        dgm_logger.info(f"Kernel: Current capabilities mapping: {list(capabilities.keys())}")
        dgm_logger.info(f"Kernel: Detected gaps: {[g.value for g in gaps]}")

        # 2. Discover Opportunities
        opportunities = self.intel_engine.discover_opportunities()
        for opp in opportunities:
            dgm_logger.info(f"Kernel: Opportunity found: {opp['name']} (Score: {opp['score']}) to fill {opp['gap_filled']}")

        # 3. Decision & Execution (if AUTO)
        if self.mode == "AUTO":
            for opp in opportunities:
                if opp["score"] >= 80:
                    dgm_logger.info(f"Kernel: Auto-importing {opp['name']}...")
                    self.importer.import_repo(opp["url"], category_override=opp["role"])

        dgm_logger.info("--- KERNEL CYCLE COMPLETE ---")

    def start(self):
        """
        Starts the continuous execution loop.
        """
        self._running = True
        dgm_logger.info(f"Live Kernel started in {self.mode} mode.")
        try:
            while self._running:
                self.run_cycle()
                time.sleep(self.interval)
        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        self._running = False
        dgm_logger.info("Live Kernel stopping...")
