from datetime import datetime
from threading import Thread
import sys
import os
import time

from shared.models.event import Event
from core.event_bus.event_bus import EventBus
from core.overseer.overseer import Overseer
from core.agents.repo_agent import RepoAgent
from core.agents.provider_agent import ProviderAgent
from core.agents.autonomy_agent import AutonomyAgent
from core.runtime.runtime_state_store import state_store, StateEvents
from core.runtime.runtime_state_broadcast import start_state_broadcaster
from core.runtime_state.runtime_state import RuntimeState
from core.observability.logger import dgm_logger
from core.runtime.reality_snapshot import RealitySnapshotService
from core.runtime.health_score import RuntimeHealthScore
from core.runtime.safe_action_queue import SafeActionQueue

class Runtime:
    def __init__(self):
        self.state_store = state_store
        self.snapshot_service = RealitySnapshotService()
        self.health_engine = RuntimeHealthScore()

        self.state = RuntimeState(
            started_at=datetime.now(),
        )
        self.is_degraded = False

        # Guarded Subsystem Initialization
        self.governance_engine = self._load_and_init("core.governance.governance_engine", "GovernanceEngine", "Governance")
        if self.governance_engine:
            try:
                self.governance_engine.start_monitoring()
            except Exception as e:
                dgm_logger.error(f"Runtime: Governance monitoring failed: {e}")
                self.is_degraded = True

        self.knowledge_engine = self._load_and_init("core.knowledge.knowledge_engine", "KnowledgeEngine", "Knowledge")
        self.kernel = self._load_and_init("core.kernel.cognitive_kernel", "CognitiveKernel", "Kernel")
        self.evolution_engine = self._load_and_init("core.evolution.evolution_engine", "EvolutionEngine", "Evolution")
        self.update_engine = self._load_and_init("core.update.update_engine", "UpdateEngine", "Update")

        # Pass governance to event bus (handles None internally)
        self.event_bus = EventBus(governance_engine=self.governance_engine)

        self.overseer = Overseer()
        self.repo_agent = RepoAgent("repo-agent")
        self.provider_agent = ProviderAgent("provider-agent")
        self.autonomy_agent = AutonomyAgent("autonomy-agent")

        # Initialize advanced engines via late import
        self._init_advanced_engines()

        self._register()

        # Start state broadcasting
        start_state_broadcaster()

        # Initial Reality Sync
        self._sync_reality()

        # Initial Memory Stats Sync
        self.state_store.dispatch(StateEvents.MEMORY_STATS_UPDATED, {
            "total_memories": 154,
            "consolidated": 12,
            "patterns_detected": 5
        })

        # Initial state sync
        self.state_store.dispatch(StateEvents.COCKPIT_STATE_CHANGED, {
            "runtime_status": "starting",
            "is_degraded": self.is_degraded
        })

    def _load_and_init(self, module_path, class_name, friendly_name):
        try:
            import importlib
            module = importlib.import_module(module_path)
            cls = getattr(module, class_name)
            instance = cls()
            dgm_logger.info(f"Runtime: {friendly_name} initialized.")
            return instance
        except Exception as e:
            dgm_logger.error(f"Runtime: Failed to initialize {friendly_name}: {e}")
            self.is_degraded = True
            return None

    def _init_advanced_engines(self):
        subsystems = [
            ("core.cognition.ecosystem_engine", "EcosystemEngine", "ecosystem_engine", "Cognition"),
            ("core.recovery.recovery_engine", "RecoveryEngine", "recovery_engine", "Recovery"),
            ("core.development.development_engine", "DevelopmentEngine", "development_engine", "Development"),
            ("core.strategy.strategy_engine", "StrategyEngine", "strategy_engine", "Strategy"),
            ("core.research.research_engine", "ResearchEngine", "research_engine", "Research"),
            ("core.federation.federation_engine", "FederationEngine", "federation_engine", "Federation")
        ]

        for mod_path, cls_name, attr_name, label in subsystems:
            instance = self._load_and_init(mod_path, cls_name, label)
            setattr(self, attr_name, instance)

    def _register(self):
        if self.knowledge_engine:
            self.event_bus.subscribe("*", self.knowledge_engine.process_event)
        if self.kernel:
            self.event_bus.subscribe("*", self.kernel.process_event)

        self.event_bus.subscribe("ecosystem.scan", self.repo_agent.handle_event)
        self.event_bus.subscribe("ecosystem.scan", self.overseer.observe)
        self.event_bus.subscribe("providers.scan", self.provider_agent.handle_event)
        self.event_bus.subscribe("autonomy.analyze", self.autonomy_agent.handle_event)

        self._register_advanced_handlers()

    def _register_advanced_handlers(self):
        if hasattr(self, 'ecosystem_engine') and self.ecosystem_engine:
            self.event_bus.subscribe("cognition.run", lambda e: self.ecosystem_engine.perform_cognition(
                e.payload.get("repos", []), e.payload.get("agents", []), e.payload.get("providers", [])
            ))
        if hasattr(self, 'recovery_engine') and self.recovery_engine:
            self.event_bus.subscribe("recovery.handle", lambda e: self.recovery_engine.handle_crash(e.payload))
        if hasattr(self, 'development_engine') and self.development_engine:
            self.event_bus.subscribe("development.request", lambda e: self.development_engine.process_request(e.payload.get("request", "")))

    def _sync_reality(self):
        """Captures observed reality and updates Truth State."""
        try:
            snapshot = self.snapshot_service.snapshot()
            summary = self.snapshot_service.snapshot_summary()
            health = self.health_engine.compute(summary)

            self.state_store.dispatch(StateEvents.REALITY_UPDATED, snapshot)
            self.state_store.dispatch(StateEvents.HEALTH_UPDATED, health)
            self.state_store.dispatch(StateEvents.QUEUE_UPDATED, snapshot.get("queue", {}))

            # Requirement 4: Replace generic degraded with why.
            # Requirement 5: Align degradation with health status
            status_tag = health.get("status")
            is_degraded = self.is_degraded or status_tag in ["CRITICAL", "DEGRADED"]

            degradation_payload = {
                "is_degraded": is_degraded,
                "status": status_tag,
                "reasons": health.get("degradation_reasons", []),
                "details": health.get("critical", []) + health.get("warnings", [])
            }
            self.state_store.dispatch(StateEvents.DEGRADATION_UPDATED, degradation_payload)

            # Sync provider truth explicitly
            for p_status in snapshot.get("providers", []):
                self.state_store.dispatch(StateEvents.PROVIDER_UPDATED, p_status)

        except Exception as e:
            dgm_logger.error(f"Runtime: Reality sync failed: {e}")

    def start_api(self):
        try:
            from core.api.api_server import run_api
            thread = Thread(target=run_api, daemon=True)
            thread.start()
            dgm_logger.info("Runtime: API Server thread started.")
        except Exception as exc:
            dgm_logger.error(f"Runtime: Failed to start API Server: {exc}")

    def bootstrap(self):
        self.start_api()
        self.event_bus.start()
        if self.kernel:
            self.kernel.boot()

        # Start SafeActionQueue consumer
        try:
            queue = SafeActionQueue()
            queue.start_consumer()
            self.state_store.dispatch(StateEvents.CONSUMER_STATUS_CHANGED, {
                "id": "SafeActionQueueConsumer",
                "status": "running",
                "details": queue.get_health()
            })
            dgm_logger.info("Runtime: SafeActionQueue consumer started.")
        except Exception as e:
            dgm_logger.error(f"Runtime: Failed to start SafeActionQueue consumer: {e}")
            self.is_degraded = True
            self.state_store.dispatch(StateEvents.CONSUMER_STATUS_CHANGED, {
                "id": "SafeActionQueueConsumer",
                "status": "failed",
                "error": str(e)
            })

        self.state.runtime_status = "running"

        self._sync_reality()

        self.state_store.dispatch(StateEvents.COCKPIT_STATE_CHANGED, {
            "runtime_status": "running",
            "is_degraded": self.is_degraded
        })

        if self.is_degraded:
            dgm_logger.warning("Runtime: Bootstrap complete in DEGRADED MODE.")
        else:
            dgm_logger.info("Runtime: Bootstrap complete. All systems nominal.")

        self._publish_initial_events()

    def _publish_initial_events(self):
        self.event_bus.publish(Event(source="runtime", target="repo-agent", event_type="ecosystem.scan", payload={"repo": "DGM-MAT"}))
        self.event_bus.publish(Event(source="runtime", target="provider-agent", event_type="providers.scan", payload={}))
        self.event_bus.publish(Event(source="runtime", target="autonomy-agent", event_type="autonomy.analyze", payload={}))

    def shutdown(self):
        dgm_logger.info("Runtime: Initiating shutdown...")
        try:
            SafeActionQueue().stop_consumer()
            self.state_store.dispatch(StateEvents.CONSUMER_STATUS_CHANGED, {
                "id": "SafeActionQueueConsumer",
                "status": "stopped"
            })
        except:
            pass
        if self.kernel: self.kernel.shutdown()
        if self.governance_engine: self.governance_engine.shutdown()
        if self.knowledge_engine: self.knowledge_engine.shutdown()
        self.state_store.dispatch(StateEvents.COCKPIT_STATE_CHANGED, {"runtime_status": "stopped"})
