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

        event = Event(
            source="runtime",
            target="repo-agent",
            event_type="repo.scan",
            payload={
                "repo": "DGM-MAT"
            },
        )
        self.event_bus.publish(event)
