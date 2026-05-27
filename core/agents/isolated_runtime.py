import threading
import time
import queue
import traceback
from typing import Any, Callable, Dict, Optional
from core.observability.logger import dgm_logger

class AgentIsolatedContext:
    """
    Isolated execution context for an agent.
    Provides crash containment and resource monitoring (Phase 42.3-LITE).
    """
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.task_queue = queue.Queue()
        self.health_status = "idle"
        self.last_crash: Optional[str] = None
        self.resource_usage = {"cpu": 0.0, "memory": 0.0}

    def start(self):
        """Starts the isolated agent loop in a separate thread."""
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._run_loop, name=f"Agent-{self.agent_id}", daemon=True)
        self.thread.start()
        dgm_logger.info(f"IsolatedRuntime: Agent {self.agent_id} started.")

    def stop(self):
        self.running = False
        self.health_status = "stopped"

    def submit_task(self, task_fn: Callable, *args, **kwargs):
        """Submits a task to the agent's isolated queue."""
        self.task_queue.put((task_fn, args, kwargs))

    def _run_loop(self):
        while self.running:
            try:
                self.health_status = "waiting"
                try:
                    task_fn, args, kwargs = self.task_queue.get(timeout=1.0)
                except queue.Empty:
                    continue

                self.health_status = "executing"
                task_fn(*args, **kwargs)
                self.task_queue.task_done()

            except Exception as e:
                self.health_status = "crashed"
                self.last_crash = traceback.format_exc()
                dgm_logger.error(f"IsolatedRuntime: Agent {self.agent_id} crashed: {e}\n{self.last_crash}")
                # Auto-recovery after 5 seconds
                time.sleep(5)
                self.health_status = "recovering"

class AgentRuntimeIsolation:
    """
    Manager for isolated agent contexts.
    """
    def __init__(self):
        self.contexts: Dict[str, AgentIsolatedContext] = {}

    def get_context(self, agent_id: str) -> AgentIsolatedContext:
        if agent_id not in self.contexts:
            self.contexts[agent_id] = AgentIsolatedContext(agent_id)
            self.contexts[agent_id].start()
        return self.contexts[agent_id]

# Global manager
isolation_layer = AgentRuntimeIsolation()
