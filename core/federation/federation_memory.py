import json
from core.storage.storage_manager import RuntimeStorageManager

class FederationMemory:
    def __init__(self, storage_manager: RuntimeStorageManager = None):
        self.storage_manager = storage_manager or RuntimeStorageManager()

    def share_knowledge(self, knowledge_id: str, knowledge_data: dict):
        self.storage_manager.save_data(
            "federation",
            f"knowledge_{knowledge_id}.json",
            json.dumps(knowledge_data, indent=2)
        )
