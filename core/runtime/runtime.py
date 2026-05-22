from shared.models.event import Event

from core.event_bus.event_bus import EventBus

from core.overseer.overseer import Overseer

from core.agents.repo_agent import RepoAgent


class Runtime:

    def __init__(self):

        self.event_bus = EventBus()

        self.overseer = Overseer()

        self.repo_agent = RepoAgent(
            "repo-agent"
        )

        self._register()

    def _register(self):

        self.event_bus.subscribe(
            "repo.scan",
            self.repo_agent.handle_event,
        )

        self.event_bus.subscribe(
            "repo.scan",
            self.overseer.observe,
        )

    def bootstrap(self):

        event = Event(
            source="runtime",
            target="repo-agent",
            event_type="repo.scan",
            payload={
                "repo": "DGM-MAT"
            },
        )

        self.event_bus.publish(event)

        self.event_bus.process()
