import json
from core.storage.storage_manager import RuntimeStorageManager

class ExperimentMemory:
    def __init__(self, storage_manager: RuntimeStorageManager = None):
        self.storage_manager = storage_manager or RuntimeStorageManager()

    def record_result(self, result: dict):
        self.storage_manager.save_data(
            "sandbox",
            f"experiment_{result.get('id', 'unknown')}.json",
            json.dumps(result, indent=2)
        )
