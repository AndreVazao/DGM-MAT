from core.providers.chatgpt.chatgpt_provider import (
    ChatGPTProvider,
)

from core.providers.conversation_classifier import (
    ConversationClassifier,
)

from core.providers.conversation_memory import (
    ConversationMemory,
)


class ProviderRuntime:

    def run(self):

        provider = ChatGPTProvider()

        conversations = (
            provider.list_conversations()
        )

        conversations = (
            ConversationClassifier()
            .classify(conversations)
        )

        ConversationMemory().persist(
            conversations
        )

        print("\n")

        print("=" * 60)

        print(
            "CONVERSATIONS DETECTED"
        )

        print("=" * 60)

        for convo in conversations:

            print(
                f"{convo.title} "
                f"-> "
                f"{convo.detected_projects}"
            )
