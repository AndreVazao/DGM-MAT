import asyncio
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.autonomy.active_runtime.cognition_loop import CognitionLoop
from core.runtime.safe_action_queue import SafeActionQueue
from core.observability.logger import dgm_logger
from core.observability.trace_utils import trace_runtime_activation

trace_runtime_activation("RUNTIME_ENTRY:scripts/autostart/start_daemon.py")


async def start():
    dgm_logger.info("Phase 37: Starting Autonomous Daemon...")
    loop = CognitionLoop()
    queue = SafeActionQueue()
    queue.start_consumer()

    trace_runtime_activation("TRACE_RUNTIME_OWNER:CognitionLoop:core/autonomy/active_runtime/cognition_loop.py")
    trace_runtime_activation("TRACE_RUNTIME_ACTIVATE:core.autonomy.active_runtime.cognition_loop")
    trace_runtime_activation("TRACE_RUNTIME_OWNER:SafeActionQueue:core/runtime/safe_action_queue.py")
    trace_runtime_activation("TRACE_RUNTIME_ACTIVATE:SafeActionQueueConsumer")

    try:
        await loop.start()
    finally:
        loop.stop()
        queue.stop_consumer()


if __name__ == "__main__":
    asyncio.run(start())
