from core.execution_fabric.task_dispatcher import TaskDispatcher
from core.execution_fabric.execution_supervisor import ExecutionSupervisor
from core.execution_fabric.execution_cycles import ExecutionCycles
from core.execution_fabric.execution_memory import ExecutionMemory

class ExecutionFabric:
    """
    Unified entry point for the DGM-MAT Autonomous Execution Fabric.
    """
    def __init__(self):
        self.dispatcher = TaskDispatcher()
        self.supervisor = ExecutionSupervisor()
        self.cycles = ExecutionCycles()
        self.memory = ExecutionMemory()

    def start(self):
        self.cycles.start_loop()
