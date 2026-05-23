from typing import List
from core.strategy.roadmap_models import StrategicObjective, TechnicalDebt, PriorityCategory

class PriorityEngine:
    def prioritize(
        self,
        objectives: List[StrategicObjective],
        debt: List[TechnicalDebt],
        sustainability: float
    ) -> List[StrategicObjective]:
        # Simple prioritization logic: debt remediation first if sustainability is low
        if sustainability < 0.5:
            for d in debt:
                # In a real scenario, convert debt to objectives
                pass

        return sorted(objectives, key=lambda x: x.priority, reverse=True)
