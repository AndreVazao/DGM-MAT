class ConversationIndexer:
    """
    Deprecated: Preserving for backward compatibility.
    """
    def index_conversation(self, cid, content):
        from core.provider_sync.conversation_indexer import ProviderConversationIndexer
        return ProviderConversationIndexer().index(cid, content)
