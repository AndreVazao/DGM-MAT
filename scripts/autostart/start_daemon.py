import asyncio
from core.autonomy.active_runtime.cognition_loop import CognitionLoop
from core.observability.logger import dgm_logger
from core.observability.trace_utils import trace_runtime_activation

trace_runtime_activation("RUNTIME_ENTRY:scripts/autostart/start_daemon.py")

async def start():
    dgm_logger.info("Phase 37: Starting Autonomous Daemon...")
    loop = CognitionLoop()
    trace_runtime_activation("TRACE_RUNTIME_OWNER:CognitionLoop:core/autonomy/active_runtime/cognition_loop.py")
    trace_runtime_activation("TRACE_RUNTIME_ACTIVATE:core.autonomy.active_runtime.cognition_loop")
    await loop.start()

if __name__ == "__main__":
    asyncio.run(start())
