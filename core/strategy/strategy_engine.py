from typing import List, Dict, Any
from core.strategy.roadmap_engine import RoadmapEngine
from core.strategy.priority_engine import PriorityEngine
from core.strategy.debt_predictor import DebtPredictor
from core.strategy.sustainability_engine import SustainabilityEngine
from core.strategy.strategy_snapshot import StrategySnapshot
from core.observability.logger import dgm_logger

class StrategyEngine:
    def __init__(self):
        self.roadmap_engine = RoadmapEngine()
        self.priority_engine = PriorityEngine()
        self.debt_predictor = DebtPredictor()
        self.sustainability_engine = SustainabilityEngine()

    def generate_strategy(self, ecosystem_data: Dict[str, Any]) -> StrategySnapshot:
        dgm_logger.info("Generating strategic orchestration plan...")

        # Predict technical debt
        debt = self.debt_predictor.forecast_debt(ecosystem_data)

        # Calculate sustainability
        sustainability = self.sustainability_engine.calculate_sustainability(ecosystem_data)

        # Prioritize actions
        objectives = self.roadmap_engine.get_objectives()
        prioritized = self.priority_engine.prioritize(objectives, debt, sustainability)

        snapshot = StrategySnapshot(
            active_objectives=prioritized,
            pending_milestones=self.roadmap_engine.get_milestones(),
            detected_debt=debt,
            sustainability_index=sustainability,
            ecosystem_health=ecosystem_data.get("health", 0.0),
            risk_forecast={"debt_urgency": "high" if debt else "low"}
        )

        dgm_logger.info(f"Strategic plan generated. Sustainability Index: {sustainability}")
        return snapshot
