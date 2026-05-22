import json
import datetime
from typing import Dict, Any, List, Optional
from core.event_bus.bus import Event, EventBus
from core.memory.engine import MemoryEngine

class KnowledgeProcessor:
    def __init__(self, event_bus: EventBus, memory_engine: MemoryEngine):
        self.bus = event_bus
        self.memory = memory_engine
        self.category = "integrated_knowledge"
        self.bus.subscribe("external_consultation_response", self._handle_response)

    def _handle_response(self, event: Event):
        raw_response = event.payload.get("response")
        gap_context = event.payload.get("gap_context", {})

        try:
            # 1. Clean and Parse
            knowledge_data = json.loads(raw_response)

            # 2. Validate
            if not self._validate_knowledge(knowledge_data):
                self._log("Invalid knowledge format received", level="error")
                return

            # 3. Structure
            integrated_entry = {
                "timestamp": datetime.datetime.utcnow().isoformat(),
                "gap_category": gap_context.get("category"),
                "original_agent": gap_context.get("agent_id"),
                "solution": knowledge_data.get("solution"),
                "type": knowledge_data.get("integration_type"),
                "confidence": knowledge_data.get("confidence"),
                "trace_id": event.trace_id
            }

            # 4. Store
            filepath = self.memory.save_snapshot(self.category, integrated_entry)
            self._log(f"Knowledge integrated and stored at {filepath}")

            # 5. Map to Ecosystem Entities & Publish
            self.bus.publish(Event(
                source="knowledge_processor",
                type="knowledge_integrated",
                payload=integrated_entry,
                priority="high",
                trace_id=event.trace_id
            ))

            # Also record as evolution event if high confidence
            if integrated_entry["confidence"] > 0.8:
                self.bus.publish(Event(
                    source="knowledge_processor",
                    type="system_improvement",
                    payload={
                        "description": f"Integrated new {integrated_entry['type']} knowledge for {integrated_entry['gap_category']}",
                        "is_evolution": True,
                        "details": integrated_entry
                    },
                    priority="medium",
                    trace_id=event.trace_id
                ))

        except json.JSONDecodeError:
            self._log("Failed to decode external AI response as JSON", level="error")

    def _validate_knowledge(self, data: Dict[str, Any]) -> bool:
        required = ["solution", "integration_type", "confidence"]
        return all(k in data for k in required)

    def _log(self, message: str, level: str = "info"):
        self.bus.publish(Event(
            source="knowledge_processor",
            type="log",
            payload={"message": message, "category": "knowledge_integration", "level": level},
            priority="low"
        ))
