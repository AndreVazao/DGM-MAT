class ProviderSync:
    """
    Deprecated: Preserving for backward compatibility.
    """
    def sync_providers(self):
        from core.provider_sync.provider_memory_sync import ProviderMemorySync
        return ProviderMemorySync().sync_all()
