from datetime import datetime
from threading import Thread

from shared.models.event import Event
from core.event_bus.event_bus import (
    EventBus,
)
from core.overseer.overseer import (
    Overseer,
)
from core.agents.repo_agent import (
    RepoAgent,
)
from core.agents.provider_agent import (
    ProviderAgent,
)
from core.lifecycle.bootstrap import (
    bootstrap_environment,
)
from core.runtime_state.runtime_state import (
    RuntimeState,
)
from core.api.api_server import run_api

class Runtime:
    def __init__(self):
        bootstrap_environment()
        self.state = RuntimeState(
            started_at=datetime.now(),
        )
        self.event_bus = EventBus()
        self.overseer = Overseer()
        self.repo_agent = RepoAgent(
            "repo-agent"
        )
        self.provider_agent = ProviderAgent(
            "provider-agent"
        )
        self._register()

    def _register(self):
        self.event_bus.subscribe(
            "ecosystem.scan",
            self.repo_agent.handle_event,
        )
        self.event_bus.subscribe(
            "ecosystem.scan",
            self.overseer.observe,
        )
        self.event_bus.subscribe(
            "providers.scan",
            self.provider_agent.handle_event,
        )

    def start_api(self):
        thread = Thread(
            target=run_api,
            daemon=True,
        )
        thread.start()

    def bootstrap(self):
        self.start_api()
        self.event_bus.start()
        self.state.runtime_status = "running"

        repo_event = Event(
            source="runtime",
            target="repo-agent",
            event_type="ecosystem.scan",
            payload={
                "repo": "DGM-MAT"
            },
        )
        self.event_bus.publish(repo_event)

        provider_event = Event(
            source="runtime",
            target="provider-agent",
            event_type="providers.scan",
            payload={},
        )
        self.event_bus.publish(provider_event)
