from dataclasses import dataclass, field

@dataclass
class Conversation:
    provider: str
    conversation_id: str
    title: str
    url: str
    tags: list[str] = field(default_factory=list)
    detected_projects: list[str] = field(default_factory=list)
