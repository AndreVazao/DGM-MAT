class ConversationLinker:
    """
    Links conversations/prompts to specific projects or files.
    """
    def __init__(self):
        self.links = {}

    def link_conversation(self, conversation_id: str, project_name: str):
        if project_name not in self.links:
            self.links[project_name] = []
        self.links[project_name].append(conversation_id)
