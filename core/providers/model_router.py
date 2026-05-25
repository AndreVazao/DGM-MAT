from typing import Dict, Any, List, Optional
from core.observability.logger import dgm_logger

class ModelRouter:
    """
    Routes tasks to the most appropriate AI model based on task type and availability.
    """
    def __init__(self, local_fabric):
        self.local_fabric = local_fabric
        self.routing_table = {
            "coding": ["ollama/llama3", "openai/gpt-4"],
            "planning": ["ollama/mistral", "openai/gpt-4o"],
            "summarization": ["ollama/phi3", "openai/gpt-3.5-turbo"],
            "reasoning": ["ollama/deepseek-coder", "openai/o1-preview"]
        }

    def route_task(self, task_category: str) -> Optional[Dict[str, str]]:
        """
        Returns the best available model for the given task category.
        """
        candidates = self.routing_table.get(task_category, ["ollama/llama3"])

        local_models = self.local_fabric.discover_local_models()

        for candidate in candidates:
            if "/" not in candidate:
                continue

            provider_name, model_name = candidate.split("/", 1)

            if provider_name in local_models:
                # Check if model exists locally
                if any(model_name in m for m in local_models[provider_name]):
                    return {"provider": provider_name, "model": model_name}

            # If not local, and external allowed (hypothetical logic)
            if provider_name == "openai":
                # Check if API key exists etc.
                return {"provider": "openai", "model": model_name}

        # Fallback to first available local model
        for p_name, models in local_models.items():
            if models:
                return {"provider": p_name, "model": models[0]}

        return None

    def health(self) -> Dict[str, Any]:
        return {
            "local_connectivity": bool(self.local_fabric.discover_local_models()),
            "routing_rules_count": len(self.routing_table)
        }

    def metrics(self) -> Dict[str, Any]:
        return {
            "routing_decisions": 0 # Placeholder
        }
