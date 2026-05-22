from typing import Any
from core.agents.base import BaseAgent
from core.event_bus.bus import Event, EventBus
from core.prompt_intelligence.generator import PromptGenerator

class PromptIntelligenceAgent(BaseAgent):
    def __init__(self, agent_id: str, event_bus: EventBus, state_manager: Any):
        super().__init__(agent_id, "prompt_intelligence", event_bus)
        self.generator = PromptGenerator(state_manager)
        self.bus.subscribe("gap_detected", self._handle_gap_detected)

    def _handle_gap_detected(self, event: Event):
        self._log(f"Handling gap detection from {event.payload.get('agent_id')}")

        provider = event.payload.get("preferred_provider", "default")
        prompt = self.generator.generate_prompt(event.payload, provider)
        optimized_prompt = self.generator.optimize_for_provider(prompt, provider)

        self.bus.publish(Event(
            source=self.id,
            type="external_consultation_request",
            payload={
                "prompt": optimized_prompt,
                "provider": provider,
                "gap_context": event.payload,
                "trace_id": event.trace_id
            },
            priority="high",
            trace_id=event.trace_id
        ))

    def execute_logic(self, task: Event) -> Any:
        if task.payload.get("task_type") == "generate_prompt":
            prompt = self.generator.generate_prompt(task.payload.get("gap_context", {}))
            return {"prompt": prompt}
        return "Prompt Intelligence logic executed"
