from typing import List
from core.strategy.roadmap_models import StrategicObjective, Milestone, PlanningHorizon, PriorityCategory

class RoadmapEngine:
    def __init__(self):
        self.objectives = []
        self.milestones = []

    def get_objectives(self) -> List[StrategicObjective]:
        # Implementation would typically fetch from storage
        return self.objectives

    def get_milestones(self) -> List[Milestone]:
        return self.milestones

    def add_objective(self, objective: StrategicObjective):
        self.objectives.append(objective)
