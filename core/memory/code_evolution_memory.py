import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from core.storage.storage_manager import storage_manager
from core.observability.logger import dgm_logger

class EvolutionEvent(BaseModel):
    event_id: str
    timestamp: datetime = Field(default_factory=datetime.now)
    type: str # decision, fix, failure, optimization
    description: str
    outcome: str # success, failure, neutral
    affected_components: List[str]
    reasoning: str
    patch_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class CodeEvolutionMemory:
    """
    Tracks architectural decisions, execution outcomes, and optimization history.
    Provides historical reasoning and repeated-error prevention.
    """
    def __init__(self):
        self.storage = storage_manager
        self.evolution_domain = "evolution_memory"
        self.history_filename = "evolution_history.json"
        self.history: List[EvolutionEvent] = self._load_history()

    def _load_history(self) -> List[EvolutionEvent]:
        content = self.storage.read_data(self.evolution_domain, self.history_filename)
        if content:
            try:
                data = json.loads(content)
                return [EvolutionEvent(**e) for e in data]
            except Exception as e:
                dgm_logger.error(f"CodeEvolutionMemory: Failed to load history: {e}")
        return []

    def _save_history(self):
        data = [e.model_dump(mode="json") for e in self.history]
        self.storage.save_data(self.evolution_domain, self.history_filename, json.dumps(data, indent=2))

    def record_event(self,
                     event_type: str,
                     description: str,
                     outcome: str,
                     affected_components: List[str],
                     reasoning: str,
                     metadata: Dict[str, Any] = None):
        """Records a new evolution event."""
        event = EvolutionEvent(
            event_id=f"ev_{datetime.now().strftime('%Y%m%d%H%M%S')}_{len(self.history)}",
            type=event_type,
            description=description,
            outcome=outcome,
            affected_components=affected_components,
            reasoning=reasoning,
            metadata=metadata or {}
        )
        self.history.append(event)
        self._save_history()
        dgm_logger.info(f"CodeEvolutionMemory: Recorded {event_type} event: {description}")

    def get_related_failures(self, components: List[str]) -> List[EvolutionEvent]:
        """Retrieves failed events related to specific components."""
        return [e for e in self.history if e.outcome == "failure" and any(c in e.affected_components for c in components)]

    def analyze_improvement_trends(self) -> Dict[str, Any]:
        """Analyzes trends in success rates and optimization outcomes."""
        if not self.history:
            return {"status": "no history"}

        success_count = sum(1 for e in self.history if e.outcome == "success")
        failure_count = sum(1 for e in self.history if e.outcome == "failure")

        return {
            "total_events": len(self.history),
            "success_rate": success_count / len(self.history),
            "failure_rate": failure_count / len(self.history),
            "recent_optimizations": [e.description for e in self.history[-5:] if e.type == "optimization"]
        }

    def get_rollback_intelligence(self, event_id: str) -> Optional[Dict[str, Any]]:
        """Provides intelligence for rolling back a specific evolution event."""
        event = next((e for e in self.history if e.event_id == event_id), None)
        if not event:
            return None

        return {
            "event_id": event_id,
            "components_to_revert": event.affected_components,
            "original_reasoning": event.reasoning,
            "risk_assessment": "Low" if event.type == "optimization" else "Medium"
        }

# Singleton instance
evolution_memory = CodeEvolutionMemory()
