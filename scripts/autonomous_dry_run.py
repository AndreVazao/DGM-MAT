import asyncio
import json
from core.autonomy.active_runtime.cognition_loop import CognitionLoop
from core.observability.logger import dgm_logger

async def run_dry_run(cycles: int = 3):
    dgm_logger.info(f"STARTING AUTONOMOUS DRY RUN ({cycles} cycles)...")
    loop = CognitionLoop()

    for i in range(cycles):
        dgm_logger.info(f"--- DRY RUN CYCLE {i+1} ---")
        await loop.run_cycle()

    dgm_logger.info("DRY RUN COMPLETE. Verifying telemetry...")
    # Check if cycle files exist in storage
    storage_path = loop.storage_path
    cycle_files = list(storage_path.glob("cycle_*.json"))
    dgm_logger.info(f"Found {len(cycle_files)} persisted cycle records.")
    assert len(cycle_files) >= cycles

if __name__ == "__main__":
    asyncio.run(run_dry_run(2))
