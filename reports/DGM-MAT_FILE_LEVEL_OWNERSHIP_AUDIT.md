# DGM-MAT FILE-LEVEL OWNERSHIP AUDIT
## 2026-10-06

> No files moved. Evidence map for migration only.

## Summary
- cockpit: 55 Python files
- core: 590 Python files
- legacy: 48 Python files
- scripts: 29 Python files
- shared: 4 Python files
- tests: 84 Python files
- tools: 7 Python files

## Highest internal coupling files
| File | Proposed owner | Internal imports | Imports | Path literals |
|---|---|---:|---|---|
| tests/import_fabric/test_phase15_16_17_import.py | tests follow destination | 36 | core.execution.worktree_manager, core.execution.branch_manager, core.execution.execution_engine, core.execution.execution_context, core.execution.approval_manager, core.execution.r |  |
| core/governance/governance_engine.py | DGM-Core-Backend | 18 | shared.models.event, shared.enums.event_priority, core.observability.logger, core.governance.runtime_limits, core.governance.event_governor, core.governance.loop_detector, core.gov |  |
| cockpit/main_window.py | DGM-Cockpit-Frontend | 16 | cockpit.widgets.dashboard_widget, cockpit.widgets.agent_widget, cockpit.widgets.mission_widget, cockpit.widgets.command_console, cockpit.widgets.runtime_health_widget, cockpit.widg |  |
| core/runtime/runtime.py | DGM-Core-Backend | 15 | shared.models.event, core.event_bus.event_bus, core.overseer.overseer, core.agents.repo_agent, core.agents.provider_agent, core.agents.autonomy_agent, core.runtime.runtime_state_st |  |
| core/knowledge/knowledge_engine.py | DGM-Core-Backend | 13 | shared.models.event, core.knowledge.knowledge_models, core.knowledge.semantic_graph, core.knowledge.semantic_memory, core.knowledge.concept_extractor, core.knowledge.context_linker |  |
| core/api/runtime_api.py | DGM-Core-Backend | 11 | core.storage.storage_manager, core.repository_cognition.repo_scanner, core.autonomy.mission_engine, core.workspace.workspace_manager, core.connectors.obsidian_connector, core.runti |  |
| core/autonomy/active_runtime/cognition_loop.py | DGM-Core-Backend | 11 | core.observability.logger, core.storage.storage_manager, core.autonomy.active_runtime.autonomy_cycle, core.autonomy.active_runtime.strategic_planner, core.autonomy.active_runtime.o |  |
| core/cognition/ecosystem_engine.py | DGM-Core-Backend | 11 | core.cognition.topology_engine, core.cognition.dependency_mapper, core.cognition.fragmentation_detector, core.cognition.convergence_engine, core.cognition.risk_predictor, core.cogn |  |
| legacy/tests/test_phase6.py | DGM-MAT root/review | 10 | core.event_bus.bus, core.overseer.overseer, core.self_healing.engine, core.repository_intelligence.auto_repair, core.git_engine.git_manager, core.deployment.manager, core.health.ca |  |
| core/bootstrap/runtime/bootstrap_engine.py | DGM-Core-Backend | 9 | core.observability.logger, core.bootstrap.core.bootstrap_context, core.bootstrap.runtime.bootstrap_sequence, core.bootstrap.core.environment_detector, core.bootstrap.core.bootstrap | C:/DevopGodMode, C:/ProgramasGodMode, C:/ProgramasGodMode/andreos-memory |
| legacy/tests/test_phase7.py | DGM-MAT root/review | 9 | core.event_bus.bus, core.ecosystem_state.manager, core.gap_detection.detector, core.agents.prompt_intelligence_agent, core.agents.provider_connector_agent, core.knowledge_integrati |  |
| core/recovery/recovery_engine.py | DGM-Core-Backend | 8 | core.recovery.health_monitor, core.recovery.crash_classifier, core.recovery.isolation_engine, core.recovery.runtime_recovery, core.recovery.provider_recovery, core.recovery.repair_ |  |
| core/autonomy/mission_engine.py | DGM-Core-Backend | 7 | core.autonomy.mission_models, core.storage.storage_manager, core.observability.logger, core.runtime.runtime_state_store, core.runtime.safe_action_queue, core.execution.approval_man | C:/DevopGodMode, C:/ProgramasGodMode |
| core/import_fabric/import_orchestrator.py | DGM-Core-Backend | 7 | core.import_fabric.repo_cloner, core.import_fabric.repo_classifier, core.import_fabric.repo_indexer, core.import_fabric.external_registry, core.import_fabric.repo_health, core.impo |  |
| core/repository_intelligence/repo_importer.py | DGM-Core-Backend | 7 | core.observability.logger, core.ecosystem.ecosystem_registry, core.ecosystem.ecosystem_models, core.repository_intelligence.repo_classifier, core.repository_intelligence.tech_detec |  |
| core/bootstrap/__init__.py | DGM-Core-Backend | 6 | core.bootstrap.core.bootstrap_context, core.bootstrap.core.bootstrap_storage, core.bootstrap.core.dependency_loader, core.bootstrap.core.environment_detector, core.bootstrap.runtim |  |
| core/development/development_engine.py | DGM-Core-Backend | 6 | core.development.feature_planner, core.development.implementation_engine, core.development.validation_engine, core.development.execution_fabric, core.development.development_memory |  |
| core/event_bus/event_bus.py | DGM-Core-Backend | 6 | shared.models.event, shared.enums.event_priority, core.validation.event_validator, core.observability.logger, core.storage.event_store, core.observability.event_stream |  |
| core/runtime/reality_snapshot.py | DGM-Core-Backend | 6 | core.observability.logger, core.ecosystem.ecosystem_registry, core.runtime.safe_action_queue, core.provider_sync.provider_registry, core.runtime.runtime_profile, core.runtime.runti | C:/DevopGodMode, C:/ProgramasGodMode |
| core/storage/event_store.py | DGM-Core-Backend | 6 | core.storage.database, core.storage.models, core.storage.init_db, core.contracts.compat, shared.models.event, core.observability.logger |  |
| core/strategy/strategy_engine.py | DGM-Core-Backend | 6 | core.strategy.roadmap_engine, core.strategy.priority_engine, core.strategy.debt_predictor, core.strategy.sustainability_engine, core.strategy.strategy_snapshot, core.observability. |  |
| legacy/tests/test_system.py | DGM-MAT root/review | 6 | core.event_bus.bus, core.validation.engine, core.overseer.overseer, core.agents.base, core.observability.logger, core.validation.drift |  |
| tests/integration/test_governance_sim.py | tests follow destination | 6 | shared.models.event, core.runtime.runtime, core.governance.runtime_limits, core.storage.database, core.storage.models, shared.enums.event_priority |  |
| tests/unit/test_runtime.py | tests follow destination | 6 | core.runtime.runtime, shared.models.event, core.validation.event_validator, core.storage.event_store, core.storage.database, core.storage.models |  |
| tools/import_engine.py | DGM-MAT root/review | 6 | core.repository_intelligence.repo_importer, core.repository_intelligence.intelligence_engine, core.strategy.goal_engine, core.kernel.live_kernel, core.observability.logger, core.re |  |
| cockpit/widgets/operational_dashboard.py | DGM-Cockpit-Frontend | 5 | cockpit.widgets.mission_widget, cockpit.widgets.agent_widget, cockpit.widgets.knowledge_feed_widget, cockpit.approvals.queue_widget, shared.config.settings |  |
| core/execution_fabric/autonomous_executor.py | DGM-Core-Backend | 5 | core.observability.logger, core.execution_fabric.worktree_runtime, core.execution_fabric.execution_supervisor, core.execution_fabric.safe_patch_engine, core.execution.approval_mana |  |
| core/federation/federation_engine.py | DGM-Core-Backend | 5 | core.federation.ecosystem_registry, core.federation.federation_governance, core.federation.federation_routing, core.federation.federation_models, core.observability.logger |  |
| core/kernel/cognitive_kernel.py | DGM-Core-Backend | 5 | core.kernel.kernel_models, core.kernel.execution_context, core.observability.logger, shared.models.event, core.federation.ecosystem_registry |  |
| core/kernel/live_kernel.py | DGM-Core-Backend | 5 | core.repository_intelligence.repo_importer, core.repository_intelligence.intelligence_engine, core.strategy.goal_engine, core.observability.logger, core.operator.autonomous_operato |  |
| core/research/research_engine.py | DGM-MAT-Labs | 5 | core.research.experimentation_engine, core.research.sandbox_runtime, core.research.isolation_controller, core.research.research_models, core.observability.logger |  |
| core/runtime/safe_action_queue.py | DGM-Core-Backend | 5 | core.storage.database, core.storage.models, core.storage.init_db, core.observability.logger, core.contracts.compat |  |
| core/runtime_daemon/daemon.py | DGM-Core-Backend | 5 | core.observability.logger, core.runtime_daemon.heartbeat, core.runtime_daemon.process_registry, core.runtime_daemon.watchdog, core.runtime_daemon.supervisor |  |
| scripts/runtime_smoke_test.py | DGM-MAT-Deploy or root tooling | 5 | core.bootstrap, core.runtime.runtime, core.observability.logger, shared.models.event, core.storage.storage_manager |  |
| core/api/api_server.py | DGM-Core-Backend | 4 | shared.config.settings, core.realtime.websocket_manager, core.api.runtime_api, core.api.mobile_bridge |  |
| core/autonomy/autonomous_loop.py | DGM-Core-Backend | 4 | core.observability.logger, core.autonomy.scheduler.scheduler_engine, core.repository_cognition.repo_scanner, core.autonomy.models |  |
| core/autonomy/repo_analysis_pipeline.py | DGM-Core-Backend | 4 | core.autonomy.models, core.repository_intelligence.intelligence_engine, core.storage.storage_manager, core.observability.logger |  |
| core/cognition/architecture_graph.py | DGM-Core-Backend | 4 | core.cognition.cognition_graph, core.cognition.cognition_models, core.storage.storage_manager, core.observability.logger |  |
| core/ecosystem/ecosystem_registry.py | DGM-Core-Backend | 4 | core.ecosystem.ecosystem_models, core.storage.storage_manager, core.observability.logger, core.ecosystem.ecosystem_materializer |  |
| core/ecosystem/reality_sync_engine.py | DGM-Core-Backend | 4 | core.ecosystem.ecosystem_registry, core.ecosystem.ecosystem_models, core.storage.storage_manager, core.observability.logger | C:/ProgramasGodMode |
| core/execution_fabric/execution_fabric.py | DGM-Core-Backend | 4 | core.execution_fabric.task_dispatcher, core.execution_fabric.execution_supervisor, core.execution_fabric.execution_cycles, core.execution_fabric.execution_memory |  |
| core/provider_mesh/provider_orchestrator.py | DGM-Core-Backend | 4 | core.observability.logger, core.provider_mesh.consensus_engine, core.provider_mesh.provider_ranker, core.provider_sync.provider_registry |  |
| core/repository_intelligence/intelligence_engine.py | DGM-Core-Backend | 4 | core.ecosystem.ecosystem_registry, core.ecosystem.ecosystem_models, core.observability.logger, core.repository_intelligence.external_repos |  |
| core/repository_intelligence/repo_federation.py | DGM-Core-Backend | 4 | core.storage.storage_manager, core.observability.logger, core.ecosystem.ecosystem_registry, core.ecosystem.ecosystem_models |  |
| core/repository_intelligence/scanner.py | DGM-Core-Backend | 4 | core.repository_intelligence.models, core.repository_intelligence.tech_detector, core.repository_intelligence.repo_classifier, core.observability.logger | C:/ProgramasGodMode |
| core/self_evolution/evolution_engine.py | DGM-Core-Backend | 4 | core.observability.logger, core.self_evolution.patch_candidate_generator, core.self_evolution.safety_validator, core.self_evolution.sandbox_runner |  |
| core/workspace/workspace_engine.py | DGM-Core-Backend | 4 | core.observability.logger, core.workspace.workspace_graph, core.workspace.project_identity, core.workspace.semantic_project_mapper |  |
| legacy/core/agents/memory_sync_agent.py | DGM-MAT root/review | 4 | core.agents.base, core.event_bus.bus, core.memory.engine, core.memory.sync |  |
| scripts/autostart/start_daemon.py | DGM-MAT-Deploy / DGM-MAT-OS | 4 | core.autonomy.active_runtime.cognition_loop, core.runtime.safe_action_queue, core.observability.logger, core.observability.trace_utils |  |
| scripts/fase_43_6_force_cognition.py | DGM-MAT-Deploy or root tooling | 4 | core.observability.logger, core.autonomy.mission_engine, core.runtime.safe_action_queue, core.autonomy.active_runtime.cognition_loop |  |
| scripts/phase_finalizer.py | DGM-MAT-Deploy or root tooling | 4 | core.storage.storage_manager, core.federation.ecosystem_registry, core.kernel.cognitive_kernel, core.strategy.strategic_memory |  |
| scripts/stress_test_providers.py | DGM-MAT-Deploy or root tooling | 4 | core.providers.performance.provider_routing_engine, core.providers.chatgpt.chatgpt_provider, core.providers.claude.claude_provider, core.observability.logger |  |
| tests/autonomy/test_phase37_logic.py | tests follow destination | 4 | core.autonomy.active_runtime.cognition_loop, core.planning.roadmap_engine, core.model_router.routing_engine, core.self_evolution.safety_validator |  |
| tests/import_fabric/test_import_intelligence_v7.py | tests follow destination | 4 | core.repository_intelligence.repo_importer, core.repository_intelligence.intelligence_engine, core.strategy.goal_engine, core.kernel.live_kernel |  |
| tests/import_fabric/test_repo_importer.py | tests follow destination | 4 | core.repository_intelligence.repo_importer, core.ecosystem.ecosystem_registry, core.ecosystem.ecosystem_models, core.repository_intelligence.repo_classifier |  |
| tests/integration/test_ecosystem.py | tests follow destination | 4 | core.ecosystem.ecosystem_models, core.ecosystem.ecosystem_registry, core.ecosystem.ecosystem_lifecycle, core.storage.storage_manager |  |
| tests/integration/test_ecosystem_materializer.py | tests follow destination | 4 | core.ecosystem.ecosystem_registry, core.ecosystem.ecosystem_validator, core.ecosystem.ecosystem_materializer, core.storage.storage_manager |  |
| tests/integration/test_repository_intelligence.py | tests follow destination | 4 | core.repository_intelligence.tech_detector, core.repository_intelligence.repo_classifier, core.repository_intelligence.models, core.repository_intelligence.duplicate_detector |  |
| tests/operational/test_cockpit_mission_trace.py | tests follow destination | 4 | core.api.api_server, core.runtime.runtime_state_store, core.autonomy.mission_engine, core.runtime.safe_action_queue |  |
| tests/test_phase35_autonomy.py | tests follow destination | 4 | core.autonomy.self_improvement_planner, core.autonomy.task_generator, core.autonomy.priority_engine, core.autonomy.models |  |
| tools/controlled_import.py | DGM-MAT root/review | 4 | core.observability.logger, core.ecosystem.ecosystem_registry, core.ecosystem.ecosystem_models, core.repository_intelligence.tech_detector |  |
| cockpit/providers/management_widget.py | DGM-Cockpit-Frontend | 3 | core.provider_sync.provider_registry, core.security.vault, shared.config.settings |  |
| cockpit/widgets/runtime_health_widget.py | DGM-Cockpit-Frontend | 3 | core.runtime.reality_snapshot, core.runtime.health_score, core.runtime.safe_action_queue |  |
| core/agents/autonomy_agent.py | DGM-MAT-Agents | 3 | shared.models.event, core.agents.base_agent, core.autonomy.task_engine |  |
| core/agents/provider_agent.py | DGM-MAT-Agents | 3 | shared.models.event, core.agents.base_agent, core.providers.provider_runtime |  |
| core/autonomous_dev/autonomous_dev_engine.py | DGM-Core-Backend | 3 | core.observability.logger, core.autonomous_dev.task_generator, core.autonomous_dev.roadmap_executor |  |
| core/autonomy/scheduler/execution_loop.py | DGM-Core-Backend | 3 | core.observability.logger, core.autonomy.scheduler.task_queue, core.autonomy.scheduler.retry_manager |  |
| core/autonomy/self_improvement_planner.py | DGM-Core-Backend | 3 | core.storage.storage_manager, core.observability.logger, core.cognition.cognitive_analysis_engine |  |
| core/autonomy/task_planner.py | DGM-Core-Backend | 3 | core.autonomy.models, core.autonomy.priority_engine, core.autonomy.worker_allocator |  |
| core/cognition/cognitive_analysis_engine.py | DGM-Core-Backend | 3 | core.storage.storage_manager, core.observability.logger, core.repository_intelligence.repo_federation |  |
| core/ecosystem/ecosystem_lifecycle.py | DGM-Core-Backend | 3 | core.ecosystem.ecosystem_models, core.ecosystem.ecosystem_registry, core.ecosystem.ecosystem_models |  |
| core/ecosystem/ecosystem_materializer.py | DGM-Core-Backend | 3 | core.observability.logger, core.ecosystem.ecosystem_registry, core.ecosystem.ecosystem_validator |  |
| core/ecosystem/safe_import_system.py | DGM-Core-Backend | 3 | core.ecosystem.ecosystem_registry, core.ecosystem.ecosystem_models, core.observability.logger |  |
| core/governance/event_governor.py | DGM-Core-Backend | 3 | shared.models.event, core.observability.logger, core.governance.runtime_limits |  |
| core/knowledge/semantic_memory.py | DGM-Core-Backend | 3 | core.knowledge.knowledge_models, core.storage.storage_manager, core.observability.logger |  |
| core/knowledge/semantic_search.py | DGM-Core-Backend | 3 | core.knowledge.knowledge_models, core.knowledge.memory_indexer, core.observability.logger |  |
| core/knowledge_graph/memory_consolidator.py | DGM-Core-Backend | 3 | core.observability.logger, core.memory.consolidation_engine, core.knowledge_graph.graph_store |  |
| core/observability/event_stream.py | DGM-Core-Backend | 3 | core.contracts.compat, shared.models.event, core.realtime.realtime_broadcast |  |
| core/operator/autonomous_operator.py | DGM-Core-Backend | 3 | core.observability.logger, core.operator.autonomous_scheduler, core.operator.task_daemon |  |
| core/operator/background_runtime.py | DGM-Core-Backend | 3 | core.operator.autonomous_operator, core.observability.logger, core.operator.task_daemon |  |
| core/provider_memory/relationship_manager.py | DGM-Core-Backend | 3 | core.provider_memory.models, core.provider_memory.project_manager, core.observability.logger |  |
| core/provider_sync/provider_memory_sync.py | DGM-Core-Backend | 3 | core.observability.logger, core.operator.provider_sync, core.provider_sync.provider_health |  |
| core/provider_sync/provider_registry.py | DGM-Core-Backend | 3 | core.storage.storage_manager, core.observability.logger, core.providers.base.provider_base |  |
| core/providers/browser/recovery_connectors.py | DGM-MAT-Providers | 3 | core.providers.browser.browser_manager, core.observability.logger, core.security.vault |  |
| core/providers/chatgpt/chatgpt_provider.py | DGM-MAT-Providers | 3 | core.providers.base.provider_base, core.providers.browser.browser_manager, core.observability.logger |  |
| core/providers/conversation_memory.py | DGM-MAT-Providers | 3 | core.memory.memory_store, core.memory.models, core.providers.models.conversation |  |
| core/providers/knowledge_normalizer.py | DGM-MAT-Providers | 3 | core.storage.storage_manager, core.observability.logger, core.providers.models.conversation |  |
| core/providers/performance/health_monitor.py | DGM-MAT-Providers | 3 | core.provider_sync.provider_registry, core.observability.logger, core.realtime.realtime_broadcast |  |
| core/providers/performance/provider_routing_engine.py | DGM-MAT-Providers | 3 | core.providers.base.provider_base, core.observability.logger, core.providers.performance.provider_capability_matrix |  |
| core/repository_intelligence/operational_feed.py | DGM-Core-Backend | 3 | core.autonomy.models, core.realtime.realtime_broadcast, core.observability.logger |  |
| core/sandbox/isolated_runtime.py | DGM-Core-Backend | 3 | core.observability.logger, core.execution_fabric.worktree_runtime, core.sandbox.execution_limits |  |
| core/storage/init_db.py | DGM-Core-Backend | 3 | core.storage.database, core.storage.models, core.observability.logger |  |
| core/strategy/goal_engine.py | DGM-Core-Backend | 3 | core.ecosystem.ecosystem_models, core.repository_intelligence.repo_importer, core.observability.logger |  |
| legacy/core/agents/prompt_intelligence_agent.py | DGM-MAT root/review | 3 | core.agents.base, core.event_bus.bus, core.prompt_intelligence.generator |  |
| legacy/tests/test_drift.py | DGM-MAT root/review | 3 | core.event_bus.bus, core.validation.drift, core.observability.logger |  |
| scripts/autostart/restore_sessions.py | DGM-MAT-Deploy / DGM-MAT-OS | 3 | core.storage.storage_manager, core.observability.logger, core.autonomy.mission_engine |  |
| scripts/bootstrap_tests/test_bootstrap_logic.py | DGM-MAT-Deploy or root tooling | 3 | core.bootstrap, core.bootstrap, core.storage.storage_manager |  |
| scripts/fase_43_6_force_cognition_real.py | DGM-MAT-Deploy or root tooling | 3 | core.autonomy.active_runtime.cognition_loop, core.autonomy.mission_engine, core.runtime.safe_action_queue |  |
| scripts/stress_test_memory.py | DGM-MAT-Deploy or root tooling | 3 | core.memory.memory_engine, core.memory.consolidation_engine, core.observability.logger |  |
| scripts/verify_mission_recovery.py | DGM-MAT-Deploy or root tooling | 3 | core.autonomy.mission_engine, core.autonomy.mission_models, core.observability.logger |  |
| tests/autonomy/test_engines.py | tests follow destination | 3 | core.autonomy.task_generator, core.autonomy.priority_engine, core.autonomy.models |  |
| tests/autonomy/test_mission_system.py | tests follow destination | 3 | core.autonomy.mission_engine, core.autonomy.mission_models, core.autonomy.active_runtime.objective_engine |  |
| tests/contracts/test_compat.py | tests follow destination | 3 | core.autonomy.mission_models, core.contracts.compat, shared.models.event |  |
| tests/contracts/test_cross_process_mission.py | tests follow destination | 3 | core.autonomy.mission_engine, core.storage.database, core.storage.models |  |
| tests/contracts/test_event_boundary.py | tests follow destination | 3 | core.contracts.compat, core.storage.event_store, shared.models.event |  |
| tests/contracts/test_event_bus_boundary.py | tests follow destination | 3 | core.event_bus.event_bus, core.storage.event_store, shared.models.event |  |
| tests/ecosystem/test_reality_sync.py | tests follow destination | 3 | core.ecosystem.reality_sync_engine, core.ecosystem.ecosystem_registry, core.ecosystem.ecosystem_models |  |
| tests/import_fabric/test_repo_import_validation.py | tests follow destination | 3 | core.workspace.workspace_graph, core.operator.capability_extractor, core.observability.logger |  |
| tests/integration/test_knowledge_fabric.py | tests follow destination | 3 | shared.models.event, core.runtime.runtime, core.knowledge.knowledge_models |  |
| tests/integration/test_research_layer.py | tests follow destination | 3 | core.research.research_engine, core.research.research_models, core.research.isolation_controller |  |
| tests/integration/test_strategic_orchestration.py | tests follow destination | 3 | core.strategy.strategy_engine, core.strategy.roadmap_models, core.strategy.debt_predictor |  |
| tests/provider_mesh/test_mesh_orchestration.py | tests follow destination | 3 | core.provider_mesh.consensus_engine, core.provider_mesh.provider_ranker, core.provider_sync.provider_registry |  |
| tests/test_phase35_cognition.py | tests follow destination | 3 | core.cognition.cognitive_analysis_engine, core.cognition.architecture_graph, core.cognition.pattern_extractor |  |
| tests/unit/test_provider_orchestration_new.py | tests follow destination | 3 | core.provider_sync.provider_registry, core.provider_mesh.provider_orchestrator, core.provider_mesh.capability_router |  |
| cockpit/app/app_foundation.py | DGM-Cockpit-Frontend | 2 | core.storage.storage_manager, core.observability.logger |  |
| cockpit/app/websocket_client.py | DGM-Cockpit-Frontend | 2 | core.observability.logger, cockpit.streaming.realtime_client | ws://localhost:8181/ws |
| core/agents/architect_agent.py | DGM-MAT-Agents | 2 | core.agents.base_agent, shared.models.event |  |
| core/agents/base_agent.py | DGM-MAT-Agents | 2 | shared.models.event, core.observability.logger |  |
| core/agents/debug_agent.py | DGM-MAT-Agents | 2 | core.agents.base_agent, shared.models.event |  |
| core/agents/devops_agent.py | DGM-MAT-Agents | 2 | core.agents.base_agent, shared.models.event |  |

## Critical boundary findings

- shared.models.event.Event is imported by Core, Cockpit and tests; strong DGM-Contracts candidate.
- shared.config.settings currently imports core.storage.storage_manager, so shared config cannot move wholesale into Contracts; split public settings/schema from Core-owned storage resolution.
- Cockpit imports Core directly in 13 locations. These are mandatory rewrites to HTTP/WebSocket/public contracts before cockpit extraction.
- MissionEngine registers a private callback with SafeActionQueue; this couples durable queue execution to a process-local MissionEngine instance and is the known cross-process risk.
- runtime_api.py imports MissionEngine, Storage, Workspace, Obsidian, StateStore, Queue and ProviderRegistry directly; it is currently an orchestration boundary, not a thin API layer.
- EventBus persists through EventStore and streams through realtime in the same publish path; durable/event-contract boundary must be separated before repo extraction.
- Hardcoded Windows paths remain in runtime/workspace/scanning code and must be centralized before extraction.
- start_daemon.py is a lifecycle entrypoint that starts both CognitionLoop and SafeActionQueue; it belongs to deployment/OS lifecycle, not Core business logic.

## Migration rule
Every row must receive explicit DESTINATION, REWRITE, OWNER/AUTHORITY and TEST before physical move. No source deletion is authorized by this report.