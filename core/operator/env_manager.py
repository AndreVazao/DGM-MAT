import os

class EnvManager:
    """
    Manages environment variables and secrets safely.
    """
    def get_env(self, key: str, default: str = None):
        return os.getenv(key, default)
