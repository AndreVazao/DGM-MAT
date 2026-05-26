from typing import Dict, Any
from core.observability.logger import dgm_logger
from core.storage.storage_manager import storage_manager

class EvolutionMemory:
    """Stores the history of system evolutions and their impacts."""
    def __init__(self):
        self.domain = "evolution_memory"

    def record_evolution(self, evolution_data: Dict[str, Any]):
        dgm_logger.info("EvolutionMemory: Recording successful system evolution.")
        filename = f"evolution_{int(time.time())}.json"
        storage_manager.save_data(self.domain, filename, str(evolution_data))
