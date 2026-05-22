from core.providers.models.conversation import (
    Conversation,
)


KEYWORDS = {
    "DGM": "DGM-MAT",
    "Baribudos": "Baribudos",
    "AndreOS": "AndreOS",
    "Jules": "Jules-MAD",
}


class ConversationClassifier:

    def classify(
        self,
        conversations: list[Conversation],
    ):

        for convo in conversations:

            title = convo.title.lower()

            for keyword, project in (
                KEYWORDS.items()
            ):

                if keyword.lower() in title:

                    convo.detected_projects.append(
                        project
                    )

                    convo.tags.append(
                        "project_related"
                    )

        return conversations
