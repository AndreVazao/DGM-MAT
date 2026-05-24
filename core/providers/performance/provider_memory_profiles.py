class ProviderMemoryProfiles:
    """
    Profiles how providers utilize context and conversation memory.
    """
    def get_memory_strategy(self, provider_id: str):
        if provider_id.startswith("gemini"):
            return "large_context"
        return "sliding_window"
