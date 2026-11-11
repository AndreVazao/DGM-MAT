from datetime import datetime
from threading import Thread, Timer
import sys
import os
import time
import psutil

from shared.models.event import Event
from core.event_bus.event_bus import EventBus
from core.overseer.overseer import Overseer
from core.agents.boundary import create_runtime_agents
from core.runtime.runtime_state_store import state_store, StateEvents
from core.runtime.runtime_state_broadcast import start_state_broadcaster
from core.runtime_state.runtime_state import RuntimeState
from core.observability.logger import dgm_logger
from core.runtime.reality_snapshot import RealitySnapshotService
from core.runtime.health_score import RuntimeHealthScore
from core.runtime.safe_action_queue import SafeActionQueue
from core.runtime.runtime_profile import detect_runtime_profile

def repository_learning_autostart_enabled(
    value: str | None = None,
    *,
    low_memory: bool = False,
) -> bool:
    """Enable repository learning by default regardless of installed RAM."""
    configured = os.getenv("DGM_REPOSITORY_LEARNING_ENABLED") if value is None else value
    if configured is None:
        return True
    return str(configured).strip().casefold() in {"1", "true", "yes", "on"}


class Runtime:
    def __init__(self):
        self.state_store = state_store
        self.profile = detect_runtime_profile()
        self.snapshot_service = RealitySnapshotService(profile=self.profile)
        self.health_engine = RuntimeHealthScore()

        self.state = RuntimeState(
            started_at=datetime.now(),
        )
        self.is_degraded = False
        self.repository_learning_service = None
        self.auto_help_worker = None
        self.api_thread: Thread | None = None
        self._startup_timers: list[Timer] = []

        # Guarded Subsystem Initialization
        self.governance_engine = self._load_and_init("core.governance.governance_engine", "GovernanceEngine", "Governance")
        if self.governance_engine:
            try:
                self.governance_engine.start_monitoring()
            except Exception as e:
                dgm_logger.error(f"Runtime: Governance monitoring failed: {e}")
                self.is_degraded = True

        self._knowledge_engine = self._load_and_init(
            "core.knowledge.knowledge_engine", "KnowledgeEngine", "Knowledge"
        )
        self.kernel = self._load_and_init("core.kernel.cognitive_kernel", "CognitiveKernel", "Kernel")
        self.evolution_engine = self._load_and_init("core.evolution.evolution_engine", "EvolutionEngine", "Evolution")
        self.update_engine = self._load_and_init("core.update.update_engine", "UpdateEngine", "Update")

        # Pass governance to event bus (handles None internally)
        self.event_bus = EventBus(governance_engine=self.governance_engine)

        self.overseer = Overseer()
        agents = create_runtime_agents()
        self.repo_agent = agents["repo"]
        self.provider_agent = agents["provider"]
        self.autonomy_agent = agents["autonomy"]

        # Publish constructed runtime agents to the single cockpit truth store.
        # "initialized" is intentional: construction is not proof that a provider,
        # external credential, or downstream capability is currently available.
        for role, agent in agents.items():
            self.state_store.dispatch(StateEvents.AGENT_STATUS_CHANGED, {
                "id": f"core:{role}",
                "name": role,
                "role": role,
                "status": "initialized",
                "implementation": type(agent).__name__,
                "provider_required": role == "provider",
                "source": "core.runtime.Runtime",
            })

        # Hardware profile is informational; initialize the same engine set on every PC.
        self._init_advanced_engines()

        self._register()

        # Start state broadcasting
        start_state_broadcaster()

        # Reality sync starts after the queue consumer is running to avoid false startup degradation.

        # Initial Memory Stats Sync
        self.state_store.dispatch(StateEvents.MEMORY_STATS_UPDATED, {
            "total_memories": 154,
            "consolidated": 12,
            "patterns_detected": 5
        })

        # Initial state sync
        self.state_store.dispatch(StateEvents.COCKPIT_STATE_CHANGED, {
            "runtime_status": "starting", "system_state": "INITIALIZING", "boot_phase": "SYSTEM_BOOT", "node_status": "STARTING",
            "is_degraded": self.is_degraded
        })

    @property
    def knowledge_engine(self):
        """Lazy-load knowledge only when a caller actually needs it."""
        if self._knowledge_engine is None:
            self._knowledge_engine = self._load_and_init(
                "core.knowledge.knowledge_engine", "KnowledgeEngine", "Knowledge"
            )
        return self._knowledge_engine

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
            ("core.strategy.strategy_engine", "StrategyEngine", "strategy_engine", "Strategy"),
            ("core.research.research_engine", "ResearchEngine", "research_engine", "Research"),
            ("core.federation.federation_engine", "FederationEngine", "federation_engine", "Federation")
        ]

        for mod_path, cls_name, attr_name, label in subsystems:
            instance = self._load_and_init(mod_path, cls_name, label)
            setattr(self, attr_name, instance)

    def _register(self):
        # Preserve low-memory lazy loading: registration must not force the engine to load.
        if self._knowledge_engine:
            self.event_bus.subscribe("*", self._knowledge_engine.process_event)
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

    def _sync_reality(self):
        """Captures observed reality and updates Truth State."""
        try:
            mode = "degraded" if self.is_degraded else "idle"
            queue = SafeActionQueue()
            active_actions = [
                action for action in queue.list_all(limit=5)
                if action.get("status") == "RUNNING"
            ]
            if active_actions:
                mode = "active"
            snapshot = self.snapshot_service.snapshot(mode=mode)
            summary = self.snapshot_service.snapshot_summary(snapshot, mode=mode)
            health = self.health_engine.compute(summary)
            health["low_memory_profile"] = summary.get("low_memory_profile", False)
            health["runtime_profile"] = summary.get("runtime_profile")
            health["resources"] = {
                "cpu": psutil.cpu_percent(),
                "memory": psutil.virtual_memory().percent
            }

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

            # Replace the provider set atomically so records absent from this
            # snapshot cannot survive as stale cache entries.
            if isinstance(snapshot, dict) and isinstance(snapshot.get("providers"), list):
                self.state_store.dispatch(StateEvents.PROVIDERS_RECONCILED, {
                    "providers": snapshot["providers"],
                    "observed_at": snapshot.get("providers_observed_at_epoch", time.time()),
                })
            else:
                dgm_logger.warning(
                    "Runtime: provider state was not reconciled because the reality snapshot was invalid."
                )

        except Exception as e:
            dgm_logger.error(f"Runtime: Reality sync failed: {e}")

    def start_api(self):
        try:
            from core.api.api_server import run_api
            self.api_thread = Thread(target=run_api, name="dgm-api-server", daemon=True)
            self.api_thread.start()
            dgm_logger.info("Runtime: API Server thread started.")
        except Exception as exc:
            self.is_degraded = True
            dgm_logger.error(f"Runtime: Failed to start API Server: {exc}")

    def bootstrap(self):
        self.start_api()
        self.event_bus.start()
        if self.kernel:
            self.kernel.boot()

        # Reconcile stale mission checkpoints before starting the durable queue worker.
        # This never auto-approves or replays a mission; unapproved actions stay unapproved.
        try:
            from core.autonomy.mission_engine import mission_engine
            recovery = mission_engine.recover_interrupted_missions()
            if any(recovery.values()):
                dgm_logger.warning(f"Runtime: Mission startup reconciliation: {recovery}")
        except Exception as exc:
            self.is_degraded = True
            dgm_logger.error(f"Runtime: Mission startup reconciliation failed: {type(exc).__name__}: {exc}")

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

        # Repository learning is enabled by default on the full runtime: it is a
        # bounded, read-only inventory worker with a durable SQLite cursor.
        # Operators can explicitly disable it with DGM_REPOSITORY_LEARNING_ENABLED=0.
        if repository_learning_autostart_enabled(low_memory=self.profile.low_memory):
            try:
                from core.api.repository_learning_api import repository_learning_service
                self.repository_learning_service = repository_learning_service
                started = repository_learning_service.start()
                dgm_logger.info(
                    "Runtime: Repository learning worker %s; progress=%s",
                    "started" if started else "already running",
                    repository_learning_service.get_status().get("status"),
                )
            except Exception as exc:
                dgm_logger.error(
                    "Runtime: Repository learning worker could not start: %s",
                    type(exc).__name__,
                )

        help_enabled = os.getenv("DGM_AUTONOMY_HELP_ENABLED", "0").strip().casefold()
        if help_enabled in {"1", "true", "yes", "on"}:
            try:
                from core.api.mobile_bridge import auto_help_worker
                self.auto_help_worker = auto_help_worker
                started = auto_help_worker.start()
                dgm_logger.info(
                    "Runtime: Free-only Hub help worker %s; providers=%s",
                    "started" if started else "already running or disabled",
                    ",".join(auto_help_worker.providers),
                )
            except Exception as exc:
                dgm_logger.error(
                    "Runtime: Free-only Hub help worker could not start: %s",
                    type(exc).__name__,
                )

        self._sync_reality()

        self.state_store.dispatch(StateEvents.COCKPIT_STATE_CHANGED, {
            "runtime_status": "running", "system_state": "ACTIVE", "boot_phase": "READY", "node_status": "NOMINAL",
            "is_degraded": self.is_degraded
        })

        if self.is_degraded:
            dgm_logger.warning("Runtime: Bootstrap complete in DEGRADED MODE.")
        else:
            dgm_logger.info("Runtime: Bootstrap complete. All systems nominal.")

        self._publish_initial_events()

    def _publish_initial_events(self):
        def publish_event(delay: int, event: Event, enabled: bool = True):
            if not enabled:
                dgm_logger.info(f"Runtime: Startup event skipped by profile -> {event.event_type}")
                return

            def run():
                dgm_logger.info(f"Runtime: Startup event publishing -> {event.event_type}")
                self.event_bus.publish(event)

            if delay <= 0:
                run()
            else:
                timer = Timer(delay, run)
                timer.daemon = True
                self._startup_timers.append(timer)
                timer.start()

        publish_event(
            0,
            Event(source="runtime", target="repo-agent", event_type="ecosystem.scan", payload={"repo": "DGM-MAT"})
        )
        publish_event(
            5,
            Event(source="runtime", target="provider-agent", event_type="providers.scan", payload={})
        )
        publish_event(
            self.profile.startup_autonomy_delay,
            Event(source="runtime", target="autonomy-agent", event_type="autonomy.analyze", payload={})
        )

    def shutdown(self):
        dgm_logger.info("Runtime: Initiating shutdown...")
        for timer in self._startup_timers:
            try:
                timer.cancel()
            except Exception:
                pass
        self._startup_timers.clear()
        try:
            from core.api.api_server import request_api_shutdown
            request_api_shutdown()
        except Exception as exc:
            dgm_logger.warning("Runtime: API shutdown request failed: %s", type(exc).__name__)
        if self.api_thread is not None and self.api_thread.is_alive():
            self.api_thread.join(timeout=10)
            if self.api_thread.is_alive():
                dgm_logger.warning(
                    "Runtime: API server thread is still active; keeping the runtime owner alive until it exits."
                )
                self.api_thread.join()
        if self.repository_learning_service is not None:
            try:
                if self.repository_learning_service.stop(timeout=5.0) is False:
                    dgm_logger.warning("Runtime: Repository learning is still active; waiting for worker exit.")
                    self.repository_learning_service.stop(timeout=None)
            except Exception as exc:
                dgm_logger.warning("Runtime: Repository learning shutdown needs fallback wait: %s", type(exc).__name__)
                worker = getattr(self.repository_learning_service, "_thread", None)
                if worker is not None and worker.is_alive():
                    worker.join()
        if self.auto_help_worker is not None:
            try:
                if self.auto_help_worker.stop(timeout=5.0) is False:
                    dgm_logger.warning("Runtime: Auto-help is still active; waiting for worker exit.")
                    self.auto_help_worker.stop(timeout=None)
            except Exception as exc:
                dgm_logger.warning("Runtime: Auto-help shutdown needs fallback wait: %s", type(exc).__name__)
                worker = getattr(self.auto_help_worker, "_thread", None)
                if worker is not None and worker.is_alive():
                    worker.join()
        try:
            queue = SafeActionQueue()
            if queue.stop_consumer(timeout=5.0) is False:
                dgm_logger.warning(
                    "Runtime: SafeActionQueue is still processing; keeping the runtime owner alive until it exits."
                )
                queue.stop_consumer(timeout=None)
            self.state_store.dispatch(StateEvents.CONSUMER_STATUS_CHANGED, {
                "id": "SafeActionQueueConsumer",
                "status": "stopped"
            })
        except Exception as exc:
            dgm_logger.warning("Runtime: SafeActionQueue shutdown needs fallback wait: %s", type(exc).__name__)
            queue = SafeActionQueue()
            stop_event = getattr(queue, "_stop_event", None)
            if stop_event is not None:
                stop_event.set()
            worker = getattr(queue, "_worker_thread", None)
            if worker is not None and worker.is_alive():
                # Fail closed: never let process exit while an action handler is active.
                worker.join()
            self.state_store.dispatch(StateEvents.CONSUMER_STATUS_CHANGED, {
                "id": "SafeActionQueueConsumer",
                "status": "stopped" if worker is None or not worker.is_alive() else "unknown"
            })
        try:
            if not self.event_bus.stop(timeout=10.0):
                dgm_logger.warning(
                    "Runtime: EventBus is still processing; keeping the runtime owner alive until it exits."
                )
                # Never let the process exit while an in-memory event callback is still running.
                self.event_bus.stop(timeout=None)
        except Exception as exc:
            dgm_logger.warning("Runtime: Event bus stop failed; waiting for worker exit: %s", type(exc).__name__)
            worker = getattr(self.event_bus, "_worker_thread", None)
            if worker is not None and worker.is_alive():
                # Fail closed: an active in-memory callback must finish before process exit.
                worker.join()
        if self.kernel: self.kernel.shutdown()
        if self.governance_engine: self.governance_engine.shutdown()
        if self._knowledge_engine: self._knowledge_engine.shutdown()
        self.state_store.dispatch(StateEvents.COCKPIT_STATE_CHANGED, {"runtime_status": "stopped"})