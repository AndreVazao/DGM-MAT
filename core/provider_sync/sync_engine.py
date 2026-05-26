from typing import List, Dict, Any
from core.providers.base.provider_base import ProviderBase
from core.observability.logger import dgm_logger

class SyncEngine:
    def __init__(self, providers: List[ProviderBase]):
        self.providers = providers

    async def sync_all(self):
        """Orchestrates synchronization across all registered providers."""
        for provider in self.providers:
            try:
                dgm_logger.info(f"SyncEngine: Syncing {provider.provider_id}")
                conversations = provider.list_conversations()
                for conv in conversations:
                    provider.sync_conversation(conv['id'])
            except Exception as e:
                dgm_logger.error(f"SyncEngine: Failed to sync {provider.provider_id}: {e}")

    def get_aggregated_conversations(self) -> List[Dict[str, Any]]:
        """Returns a unified list of conversations from all providers."""
        aggregated = []
        for provider in self.providers:
            aggregated.extend(provider.list_conversations())
        return aggregated
