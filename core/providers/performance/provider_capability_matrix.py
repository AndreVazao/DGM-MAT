class ProviderCapabilityMatrix:
    """
    Maintains a matrix of provider capabilities (reasoning, coding, speed).
    """
    def __init__(self):
        self.matrix = {
            "claude-3-5-sonnet": {"coding": 9, "reasoning": 8, "speed": 7},
            "gpt-4o": {"coding": 8, "reasoning": 9, "speed": 8},
            "gemini-1.5-pro": {"context": 10, "reasoning": 7, "speed": 6}
        }
