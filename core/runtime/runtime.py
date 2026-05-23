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
from core.agents.autonomy_agent import (
    AutonomyAgent,
)
from core.lifecycle.bootstrap import (
    bootstrap_environment,
)
from core.runtime_state.runtime_state import (
    RuntimeState,
)
from core.api.api_server import run_api
from core.observability.logger import dgm_logger

# Phase 18, 19, 20 imports
try:
    from core.cognition.ecosystem_engine import EcosystemEngine
    from core.recovery.recovery_engine import RecoveryEngine
    from core.development.development_engine import DevelopmentEngine
except ImportError as exc:
    dgm_logger.error(f"Runtime: Failed to import Phase 18/19/20 modules: {exc}")
    EcosystemEngine = None
    RecoveryEngine = None
    DevelopmentEngine = None

class Runtime:
    def __init__(self):
        bootstrap_environment()
        self.state = RuntimeState(
            started_at=datetime.now(),
        )
        self.event_bus = EventBus()
        self.overseer = Overseer()
        self.repo_agent = RepoAgent("repo-agent")
        self.provider_agent = ProviderAgent("provider-agent")
        self.autonomy_agent = AutonomyAgent("autonomy-agent")

        # Initialize advanced engines with safety guards
        self.ecosystem_engine = self._init_subsystem(EcosystemEngine, "Cognition")
        self.recovery_engine = self._init_subsystem(RecoveryEngine, "Recovery")
        self.development_engine = self._init_subsystem(DevelopmentEngine, "Development")

        self._register()

    def _init_subsystem(self, cls, name):
        if cls is None:
            dgm_logger.warning(f"Runtime: {name} Engine class is missing. Subsystem disabled.")
            return None
        try:
            instance = cls()
            dgm_logger.info(f"Runtime: {name} Engine initialized successfully.")
            return instance
        except Exception as exc:
            dgm_logger.error(f"Runtime: Failed to initialize {name} Engine: {exc}")
            return None

    def _register(self):
        self.event_bus.subscribe("ecosystem.scan", self.repo_agent.handle_event)
        self.event_bus.subscribe("ecosystem.scan", self.overseer.observe)
        self.event_bus.subscribe("providers.scan", self.provider_agent.handle_event)
        self.event_bus.subscribe("autonomy.analyze", self.autonomy_agent.handle_event)

        # Guarded subscriptions
        if self.ecosystem_engine:
            self.event_bus.subscribe(
                "cognition.run",
                lambda e: self.ecosystem_engine.perform_cognition(
                    e.payload.get("repos", []),
                    e.payload.get("agents", []),
                    e.payload.get("providers", [])
                ),
            )

        if self.recovery_engine:
            self.event_bus.subscribe(
                "recovery.handle",
                lambda e: self.recovery_engine.handle_crash(e.payload),
            )

        if self.development_engine:
            self.event_bus.subscribe(
                "development.request",
                lambda e: self.development_engine.process_request(e.payload.get("request", "")),
            )

    def start_api(self):
        thread = Thread(target=run_api, daemon=True)
        thread.start()

    def bootstrap(self):
        self.start_api()
        self.event_bus.start()
        self.state.runtime_status = "running"

        # Log degradation if critical engines are missing
        if not all([self.ecosystem_engine, self.recovery_engine, self.development_engine]):
            dgm_logger.warning("Runtime: Bootstrap complete in DEGRADED MODE (some engines offline).")
        else:
            dgm_logger.info("Runtime: Bootstrap complete. All systems nominal.")

        self._publish_initial_events()

    def _publish_initial_events(self):
        self.event_bus.publish(Event(source="runtime", target="repo-agent", event_type="ecosystem.scan", payload={"repo": "DGM-MAT"}))
        self.event_bus.publish(Event(source="runtime", target="provider-agent", event_type="providers.scan", payload={}))
        self.event_bus.publish(Event(source="runtime", target="autonomy-agent", event_type="autonomy.analyze", payload={}))
