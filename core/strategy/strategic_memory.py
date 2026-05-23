import json
from core.storage.storage_manager import RuntimeStorageManager

class StrategicMemory:
    def __init__(self, storage_manager: RuntimeStorageManager = None):
        self.storage_manager = storage_manager or RuntimeStorageManager()

    def store_decision(self, decision: dict):
        # Implementation would typically store to a persistent ledger
        self.storage_manager.save_data(
            "strategy",
            f"decision_{decision.get('id', 'unknown')}.json",
            json.dumps(decision, indent=2)
        )
