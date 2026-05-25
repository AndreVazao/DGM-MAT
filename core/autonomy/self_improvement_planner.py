import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from core.storage.storage_manager import storage_manager
from core.observability.logger import dgm_logger
from core.cognition.cognitive_analysis_engine import cognitive_engine

class ImprovementGoal(BaseModel):
    goal_id: str
    category: str # stability, scalability, cognition, etc.
    title: str
    description: str
    priority: int # 0-100
    status: str = "planned"
    target_components: List[str]
    phased_plan: List[str]
    created_at: datetime = Field(default_factory=datetime.now)

class SelfImprovementPlanner:
    """
    Evaluates architecture weaknesses and generates strategic improvement goals
    and phased execution plans.
    """
    def __init__(self):
        self.storage = storage_manager
        self.roadmaps_domain = "roadmaps"
        self.goals_filename = "strategic_roadmap.json"
        self.goals: List[ImprovementGoal] = self._load_goals()

    def _load_goals(self) -> List[ImprovementGoal]:
        content = self.storage.read_data(self.roadmaps_domain, self.goals_filename)
        if content:
            try:
                data = json.loads(content)
                return [ImprovementGoal(**g) for g in data]
            except Exception as e:
                dgm_logger.error(f"SelfImprovementPlanner: Failed to load goals: {e}")
        return []

    def _save_goals(self):
        data = [g.model_dump(mode="json") for g in self.goals]
        self.storage.save_data(self.roadmaps_domain, self.goals_filename, json.dumps(data, indent=2))

    def evaluate_weaknesses(self, reports: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identifies architectural weaknesses from cognitive reports."""
        weaknesses = []
        for report in reports:
            for bottleneck in report.get("bottlenecks", []):
                weaknesses.append({
                    "repo": report.get("target_repo"),
                    "weakness": bottleneck,
                    "impact": "high"
                })
        return weaknesses

    def generate_strategic_goals(self, weaknesses: List[Dict[str, Any]]):
        """Generates long-term improvement goals based on detected weaknesses."""
        dgm_logger.info("SelfImprovementPlanner: Generating strategic goals...")

        for w in weaknesses:
            goal_id = f"goal_{len(self.goals)}_{datetime.now().strftime('%Y%m%d')}"

            # Simple goal generation logic
            goal = ImprovementGoal(
                goal_id=goal_id,
                category="stability",
                title=f"Address bottleneck: {w['weakness']}",
                description=f"Strategic improvement for {w['repo']} to eliminate {w['weakness']}",
                priority=80 if w["impact"] == "high" else 50,
                target_components=[w["repo"]],
                phased_plan=[
                    "Analyze root cause in staging",
                    "Develop isolated patch in experiments workspace",
                    "Verify with integration tests",
                    "Apply to active repository"
                ]
            )
            self.goals.append(goal)

        self._save_goals()
        dgm_logger.info(f"SelfImprovementPlanner: Generated {len(weaknesses)} new goals.")

    def get_roadmap_summary(self) -> Dict[str, Any]:
        """Returns a summary of the current strategic roadmap."""
        return {
            "total_goals": len(self.goals),
            "by_category": self._get_category_distribution(),
            "highest_priority": sorted(self.goals, key=lambda g: g.priority, reverse=True)[0].title if self.goals else None
        }

    def _get_category_distribution(self) -> Dict[str, int]:
        dist = {}
        for g in self.goals:
            dist[g.category] = dist.get(g.category, 0) + 1
        return dist

# Singleton instance
improvement_planner = SelfImprovementPlanner()
