class RuntimePersistence:
    """
    Persists local runtime state across restarts.
    """
    def save_state(self, state: dict):
        pass

    def load_state(self) -> dict:
        return {}
