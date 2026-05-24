import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from core.kernel.kernel_models import ExecutionContext
from core.observability.logger import dgm_logger

class ContextManager:
    def __init__(self):
        self.active_contexts: Dict[str, ExecutionContext] = {}

    def create_context(self,
                       runtime_state: Optional[Dict[str, Any]] = None,
                       governance_state: Optional[Dict[str, Any]] = None,
                       semantic_context: Optional[Dict[str, Any]] = None) -> ExecutionContext:
        """Creates a new unified execution context."""
        ctx_id = str(uuid.uuid4())
        ctx = ExecutionContext(
            execution_id=ctx_id,
            timestamp=datetime.now(),
            runtime_state=runtime_state or {},
            governance_state=governance_state or {},
            semantic_context=semantic_context or {}
        )
        self.active_contexts[ctx_id] = ctx
        dgm_logger.debug(f"Kernel: Created execution context {ctx_id}")
        return ctx

    def get_context(self, execution_id: str) -> Optional[ExecutionContext]:
        return self.active_contexts.get(execution_id)

    def close_context(self, execution_id: str):
        if execution_id in self.active_contexts:
            del self.active_contexts[execution_id]
            dgm_logger.debug(f"Kernel: Closed execution context {execution_id}")

    def update_context_pressure(self, execution_id: str, pressure: float):
        ctx = self.get_context(execution_id)
        if ctx:
            ctx.resource_pressure = pressure
