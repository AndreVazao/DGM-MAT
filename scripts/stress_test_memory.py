import time
import json
from pathlib import Path
from core.memory.memory_engine import MemoryEngine
from core.memory.consolidation_engine import MemoryConsolidationEngine
from core.observability.logger import dgm_logger

def run_stress_test(count: int = 1000):
    engine = MemoryEngine()
    consolidator = MemoryConsolidationEngine()

    dgm_logger.info(f"STRESS TEST: Creating {count} memories...")
    for i in range(count):
        engine.store_memory("semantic", {"concept": f"concept_{i % 100}", "value": i}, importance=0.1)

    dgm_logger.info("STRESS TEST: Running consolidation on 1k entries...")
    start = time.time()
    consolidator.consolidate()
    end = time.time()

    dgm_logger.info(f"STRESS TEST: Consolidation took {end - start:.2f}s")

if __name__ == "__main__":
    run_stress_test(1000) # Reduced from 10k for faster CI validation
