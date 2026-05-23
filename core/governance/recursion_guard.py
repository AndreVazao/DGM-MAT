import threading
from core.observability.logger import dgm_logger

class RecursionGuard:
    def __init__(self, max_depth: int = 10):
        self.max_depth = max_depth
        self.local = threading.local()

    def enter(self) -> bool:
        """Increments current recursion depth for the thread. Returns False if depth exceeded."""
        if not hasattr(self.local, 'depth'):
            self.local.depth = 0

        if self.local.depth >= self.max_depth:
            dgm_logger.error(f"RecursionGuard: Max depth {self.max_depth} reached in thread {threading.current_thread().name}")
            return False

        self.local.depth += 1
        return True

    def exit(self):
        """Decrements current recursion depth."""
        if hasattr(self.local, 'depth') and self.local.depth > 0:
            self.local.depth -= 1

    def get_depth(self) -> int:
        return getattr(self.local, 'depth', 0)
