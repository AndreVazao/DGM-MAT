import time
from contextlib import contextmanager
from core.observability.logger import dgm_logger

class RuntimeProfiler:
    @contextmanager
    def profile(self, name: str):
        start = time.perf_counter()
        yield
        duration = time.perf_counter() - start
        dgm_logger.info(f"Profiler: {name} took {duration:.4f} seconds.")
