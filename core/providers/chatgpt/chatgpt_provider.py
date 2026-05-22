from core.providers.base.provider_base import (
    ProviderBase,
)

from core.providers.browser.browser_manager import (
    BrowserManager,
)

from core.providers.models.conversation import (
    Conversation,
)


class ChatGPTProvider(
    ProviderBase
):

    def __init__(self):

        self.browser_manager = (
            BrowserManager()
        )

        self.browser = None

    def authenticate(self):

        self.browser = (
            self.browser_manager.start()
        )

        page = self.browser.new_page()

        page.goto(
            "https://chatgpt.com"
        )

        input(
            "\nLogin manually "
            "then press ENTER..."
        )

        return page

    def list_conversations(self):

        page = self.authenticate()

        conversations = []

        links = page.locator(
            "a"
        ).all()

        for link in links:

            try:

                href = (
                    link.get_attribute(
                        "href"
                    )
                )

                text = (
                    link.inner_text()
                )

                if (
                    href
                    and "/c/" in href
                ):

                    conversations.append(
                        Conversation(
                            provider="chatgpt",
                            conversation_id=href,
                            title=text,
                            url=(
                                "https://chatgpt.com"
                                f"{href}"
                            ),
                            tags=[],
                            detected_projects=[],
                        )
                    )

            except Exception:
                pass

        return conversations
