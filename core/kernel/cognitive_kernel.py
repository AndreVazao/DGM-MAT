from datetime import datetime
from typing import Dict, Any, Optional
from core.kernel.kernel_models import KernelState, KernelStatus, ExecutionContext
from core.kernel.execution_context import ContextManager
from core.observability.logger import dgm_logger
from shared.models.event import Event

class CognitiveKernel:
    """
    The central coordinator for DGM-MAT.
    Unifies cognition, governance, recovery, and execution.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CognitiveKernel, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.state = KernelState(status=KernelStatus.INITIALIZING)
        self.context_manager = ContextManager()
        self._initialized = True
        dgm_logger.info("Cognitive Kernel: Initialized.")

    def boot(self):
        """Starts the kernel operations."""
        self.state.status = KernelStatus.RUNNING
        dgm_logger.info("Cognitive Kernel: Booted and operational.")

    def process_event(self, event: Event) -> Optional[ExecutionContext]:
        """
        Main entry point for execution flows.
        Wraps event processing in a cognitive execution context.
        """
        # 1. Analyze Context
        ctx = self.context_manager.create_context(
            runtime_state={"event_type": event.event_type, "source": event.source},
            governance_state={"priority": event.priority.value if hasattr(event.priority, 'value') else event.priority}
        )

        dgm_logger.debug(f"Kernel: Processing event {event.event_type} in context {ctx.execution_id}")

        # In Phase 26, we start routing through the kernel
        return ctx

    def get_health(self) -> Dict[str, Any]:
        return {
            "status": self.state.status.value,
            "cognition_load": self.state.cognition_load,
            "orchestration_pressure": self.state.orchestration_pressure,
            "active_contexts": len(self.context_manager.active_contexts)
        }

    def shutdown(self):
        self.state.status = KernelStatus.SHUTTING_DOWN
        dgm_logger.info("Cognitive Kernel: Shutting down.")
