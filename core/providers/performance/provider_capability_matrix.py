from typing import Dict, Any, List

class ProviderCapabilityMatrix:
    """
    Detailed Capability Matrix for Phase 42.3-LITE.
    Used for intelligent task routing and automatic delegation.
    """
    def __init__(self):
        # Capabilities on a scale of 0-10
        self.matrix = {
            "chatgpt": {
                "architecture": 9.5,
                "planning": 9.0,
                "coding": 8.5,
                "reasoning": 9.0,
                "multimodal": 8.0,
                "speed": 8.0,
                "context": 128000
            },
            "claude": {
                "architecture": 9.0,
                "planning": 8.5,
                "coding": 9.0,
                "reasoning": 9.5,
                "multimodal": 7.0,
                "speed": 7.5,
                "context": 200000
            },
            "deepseek": {
                "architecture": 7.5,
                "planning": 7.0,
                "coding": 9.8, # Specialist in coding
                "reasoning": 9.2,
                "multimodal": 0.0,
                "speed": 6.5,
                "context": 64000
            },
            "gemini": {
                "architecture": 8.0,
                "planning": 8.0,
                "coding": 8.0,
                "reasoning": 8.0,
                "multimodal": 10.0, # Best multimodal
                "speed": 7.0,
                "context": 1000000
            },
            "grok": {
                "architecture": 7.0,
                "planning": 7.0,
                "coding": 7.5,
                "reasoning": 8.5,
                "realtime": 10.0, # Best for realtime web access
                "speed": 9.0,
                "context": 128000
            },
            "qwen": {
                "architecture": 7.0,
                "planning": 7.0,
                "coding": 8.5,
                "reasoning": 8.0,
                "multimodal": 6.0,
                "speed": 8.5,
                "context": 32000
            }
        }

    def get_best_provider_for(self, task_type: str) -> str:
        """Finds the best provider based on capability score."""
        best_provider = "chatgpt" # Default fallback
        best_score = -1.0

        for name, caps in self.matrix.items():
            score = caps.get(task_type, 0.0)
            if score > best_score:
                best_score = score
                best_provider = name

        return best_provider

    def get_fallback_chain(self, task_type: str) -> List[str]:
        """Returns a list of providers ordered by capability for fallback."""
        return sorted(
            self.matrix.keys(),
            key=lambda x: self.matrix[x].get(task_type, 0.0),
            reverse=True
        )

# Global matrix
capability_matrix = ProviderCapabilityMatrix()
