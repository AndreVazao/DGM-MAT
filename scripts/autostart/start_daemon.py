import asyncio
from core.autonomy.active_runtime.cognition_loop import CognitionLoop
from core.observability.logger import dgm_logger

async def start():
    dgm_logger.info("Phase 37: Starting Autonomous Daemon...")
    loop = CognitionLoop()
    await loop.start()

if __name__ == "__main__":
    asyncio.run(start())
