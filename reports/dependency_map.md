# Dependency Map
_Generated: 20260530T191704_

## External packages (top 40)
- `core`: 991
- `PySide6`: 81
- `pytest`: 66
- `shared`: 42
- `pydantic`: 35
- `cockpit`: 29
- `psutil`: 13
- `requests`: 9
- `fastapi`: 8
- `ast`: 6
- `networkx`: 6
- `sqlalchemy`: 5
- `sqlite3`: 4
- `argparse`: 4
- `playwright`: 2
- `httpx`: 2
- `uvicorn`: 2
- `difflib`: 2
- `yaml`: 2
- `shlex`: 2
- `concurrent`: 2
- `tools`: 2
- `websocket`: 1
- `websockets`: 1
- `astor`: 1
- `loguru`: 1
- `cryptography`: 1
- `scripts`: 1

## Internal dependency graph

**cockpit/app/app_foundation.py**
  - `core.observability.logger`
  - `core.storage.storage_manager`

**cockpit/app/websocket_client.py**
  - `core.observability.logger`

**cockpit/main_window.py**
  - `core.observability.logger`

**cockpit/providers/management_widget.py**
  - `core.provider_sync.provider_registry`
  - `core.security.vault`

**cockpit/streaming/realtime_client.py**
  - `core.observability.logger`

**cockpit/widgets/command_console.py**
  - `core.observability.logger`

**cockpit/widgets/federation_widget.py**
  - `core.federation.ecosystem_registry`

**cockpit/widgets/mission_widget.py**
  - `core.observability.logger`

**cockpit/widgets/runtime_health_widget.py**
  - `core.runtime.health_score`
  - `core.runtime.reality_snapshot`
  - `core.runtime.safe_action_queue`

**core/agents/architect_agent.py**
  - `core.agents.base_agent`

**core/agents/autonomy_agent.py**
  - `core.agents.base_agent`
  - `core.autonomy.task_engine`

**core/agents/base_agent.py**
  - `core.observability.logger`

**core/agents/debug_agent.py**
  - `core.agents.base_agent`

**core/agents/devops_agent.py**
  - `core.agents.base_agent`

**core/agents/isolated_runtime.py**
  - `core.observability.logger`

**core/agents/memory_agent.py**
  - `core.agents.base_agent`

**core/agents/provider_agent.py**
  - `core.agents.base_agent`
  - `core.providers.provider_runtime`

**core/agents/refactor_agent.py**
  - `core.agents.base_agent`

**core/agents/repo_agent.py**
  - `core.agents.base_agent`

**core/agents/research_agent.py**
  - `core.agents.base_agent`

**core/agents/runtime_agent.py**
  - `core.agents.base_agent`

**core/agents/security_agent.py**
  - `core.agents.base_agent`

**core/agents/self_improvement_agent.py**
  - `core.agents.base_agent`

**core/agents/specialization/adaptive_specialization.py**
  - `core.observability.logger`

**core/agents/specialization/agent_profiler.py**
  - `core.observability.logger`

**core/agents/specialization/capability_allocator.py**
  - `core.observability.logger`

**core/agents/specialization/provider_affinity.py**
  - `core.observability.logger`

**core/agents/specialization/runtime_affinity.py**
  - `core.observability.logger`

**core/agents/specialization/skill_distribution.py**
  - `core.observability.logger`

**core/agents/specialization/specialization_registry.py**
  - `core.observability.logger`

**core/agents/specialization/workload_optimizer.py**
  - `core.observability.logger`

**core/agents/ui_agent.py**
  - `core.agents.base_agent`

**core/agents/watchdog.py**
  - `core.agents.isolated_runtime`
  - `core.observability.logger`

**core/api/api_server.py**
  - `core.api.mobile_bridge`
  - `core.api.runtime_api`
  - `core.realtime.websocket_manager`

**core/api/mobile_bridge.py**
  - `core.observability.logger`
  - `core.realtime.websocket_manager`

**core/api/runtime_api.py**
  - `core.autonomy.mission_engine`
  - `core.connectors.obsidian_connector`
  - `core.provider_sync.provider_registry`
  - `core.realtime.websocket_manager`
  - `core.repository_cognition.repo_scanner`
  - `core.runtime.reality_snapshot`
  - `core.runtime.runtime_state_store`
  - `core.runtime.safe_action_queue`
  - `core.storage.storage_manager`
  - `core.workspace.workspace_manager`

**core/autonomous_dev/autonomous_dev_engine.py**
  - `core.autonomous_dev.roadmap_executor`
  - `core.autonomous_dev.task_generator`
  - `core.observability.logger`

**core/autonomous_dev/cleanup_engine.py**
  - `core.observability.logger`

**core/autonomous_dev/issue_detector.py**
  - `core.observability.logger`

**core/autonomous_dev/merge_planner.py**
  - `core.observability.logger`

**core/autonomous_dev/roadmap_executor.py**
  - `core.observability.logger`

**core/autonomous_dev/technical_debt_engine.py**
  - `core.observability.logger`

**core/autonomy/active_runtime/cognition_loop.py**
  - `core.autonomy.active_runtime.autonomy_cycle`
  - `core.autonomy.active_runtime.execution_director`
  - `core.autonomy.active_runtime.learning_loop`
  - `core.autonomy.active_runtime.objective_engine`
  - `core.autonomy.active_runtime.strategic_planner`
  - `core.autonomy.mission_engine`
  - `core.autonomy.scheduler.scheduler_engine`
  - `core.observability.logger`
  - `core.realtime.realtime_broadcast`
  - `core.repository_cognition.repo_scanner`
  - `core.storage.storage_manager`

**core/autonomy/active_runtime/execution_director.py**
  - `core.observability.logger`

**core/autonomy/active_runtime/learning_loop.py**
  - `core.observability.logger`

**core/autonomy/active_runtime/objective_engine.py**
  - `core.autonomy.mission_models`
  - `core.observability.logger`

**core/autonomy/active_runtime/strategic_planner.py**
  - `core.observability.logger`
  - `core.repository_cognition.repo_scanner`

**core/autonomy/autonomous_loop.py**
  - `core.autonomy.models`
  - `core.autonomy.scheduler.scheduler_engine`
  - `core.observability.logger`
  - `core.repository_cognition.repo_scanner`

**core/autonomy/continuous_runtime/adaptive_router.py**
  - `core.observability.logger`

**core/autonomy/continuous_runtime/autonomous_director.py**
  - `core.observability.logger`

**core/autonomy/continuous_runtime/cognition_scheduler.py**
  - `core.observability.logger`

**core/autonomy/continuous_runtime/evolution_engine.py**
  - `core.observability.logger`
  - `core.self_evolution.evolution_engine`

**core/autonomy/continuous_runtime/execution_coordinator.py**
  - `core.observability.logger`

**core/autonomy/continuous_runtime/lifecycle_manager.py**
  - `core.observability.logger`
  - `core.storage.storage_manager`

**core/autonomy/continuous_runtime/observation_engine.py**
  - `core.observability.logger`
  - `core.repository_cognition.repo_scanner`

**core/autonomy/continuous_runtime/planning_engine.py**
  - `core.observability.logger`

**core/autonomy/continuous_runtime/reflection_engine.py**
  - `core.observability.logger`

**core/autonomy/continuous_runtime/runtime_core.py**
  - `core.autonomy.continuous_runtime.lifecycle_manager`
  - `core.observability.logger`

**core/autonomy/mission_engine.py**
  - `core.autonomy.mission_models`
  - `core.observability.logger`
  - `core.realtime.realtime_broadcast`
  - `core.runtime.runtime_state_store`
  - `core.runtime.safe_action_queue`
  - `core.storage.storage_manager`

**core/autonomy/priority_engine.py**
  - `core.autonomy.models`
  - `core.observability.logger`

**core/autonomy/repo_analysis_pipeline.py**
  - `core.autonomy.models`
  - `core.observability.logger`
  - `core.repository_intelligence.intelligence_engine`
  - `core.storage.storage_manager`

**core/autonomy/safe_autonomous_executor.py**
  - `core.observability.logger`

**core/autonomy/scheduler/execution_loop.py**
  - `core.autonomy.scheduler.retry_manager`
  - `core.autonomy.scheduler.task_queue`
  - `core.observability.logger`

**core/autonomy/scheduler/scheduler_engine.py**
  - `core.autonomy.models`
  - `core.observability.logger`

**core/autonomy/scheduler/task_queue.py**
  - `core.observability.logger`
  - `core.storage.storage_manager`

**core/autonomy/self_improvement_planner.py**
  - `core.cognition.cognitive_analysis_engine`
  - `core.observability.logger`
  - `core.storage.storage_manager`

**core/autonomy/task_engine.py**
  - `core.autonomy.task_planner`
  - `core.autonomy.task_queue`

**core/autonomy/task_generator.py**
  - `core.autonomy.models`

**core/autonomy/task_planner.py**
  - `core.autonomy.models`
  - `core.autonomy.priority_engine`
  - `core.autonomy.worker_allocator`

**core/autonomy/task_queue.py**
  - `core.autonomy.scheduler.task_queue`

**core/autonomy/work_queue.py**
  - `core.autonomy.scheduler.task_queue`

**core/bootstrap/__init__.py**
  - `core.bootstrap.core.bootstrap_context`
  - `core.bootstrap.core.bootstrap_storage`
  - `core.bootstrap.core.dependency_loader`
  - `core.bootstrap.core.environment_detector`
  - `core.bootstrap.runtime.bootstrap_engine`
  - `core.bootstrap.runtime.bootstrap_sequence`

**core/bootstrap/core/bootstrap_storage.py**
  - `core.storage.init_db`
  - `core.storage.storage_manager`

**core/bootstrap/core/dependency_loader.py**
  - `core.observability.logger`

**core/bootstrap/core/environment_detector.py**
  - `core.observability.logger`

**core/bootstrap/runtime/bootstrap_engine.py**
  - `core.bootstrap.core.bootstrap_context`
  - `core.bootstrap.core.bootstrap_storage`
  - `core.bootstrap.core.dependency_loader`
  - `core.bootstrap.core.environment_detector`
  - `core.bootstrap.runtime.bootstrap_sequence`
  - `core.observability.logger`
  - `core.runtime.runtime_state_store`
  - `core.storage.storage_manager`

**core/cockpit_runtime/cognition_visualizer.py**
  - `core.cockpit_runtime.websocket_runtime`

**core/cockpit_runtime/execution_dashboard.py**
  - `core.autonomy.scheduler.task_queue`

**core/cockpit_runtime/live_task_feed.py**
  - `core.cockpit_runtime.websocket_runtime`

**core/cockpit_runtime/realtime_runtime_api.py**
  - `core.observability.logger`

**core/cockpit_runtime/telemetry_stream.py**
  - `core.cockpit_runtime.websocket_runtime`
  - `core.observability.logger`

**core/cockpit_runtime/websocket_runtime.py**
  - `core.observability.logger`

**core/cognition/architecture_graph.py**
  - `core.cognition.cognition_graph`
  - `core.cognition.cognition_models`
  - `core.observability.logger`
  - `core.storage.storage_manager`

**core/cognition/architecture_memory.py**
  - `core.cognition.cognition_snapshot`
  - `core.storage.storage_manager`

**core/cognition/cognition_graph.py**
  - `core.cognition.cognition_models`
  - `core.observability.logger`

**core/cognition/cognition_snapshot.py**
  - `core.cognition.cognition_models`

**core/cognition/cognitive_analysis_engine.py**
  - `core.observability.logger`
  - `core.repository_intelligence.repo_federation`
  - `core.storage.storage_manager`

**core/cognition/dependency_mapper.py**
  - `core.cognition.cognition_models`

**core/cognition/ecosystem_engine.py**
  - `core.cognition.architecture_memory`
  - `core.cognition.cognition_models`
  - `core.cognition.cognition_snapshot`
  - `core.cognition.convergence_engine`
  - `core.cognition.dependency_mapper`
  - `core.cognition.ecosystem_health`
  - `core.cognition.fragmentation_detector`
  - `core.cognition.impact_analyzer`
  - `core.cognition.risk_predictor`
  - `core.cognition.topology_engine`
  - `core.observability.logger`

**core/cognition/ecosystem_health.py**
  - `core.cognition.cognition_models`

**core/cognition/fragmentation_detector.py**
  - `core.cognition.cognition_models`

**core/cognition/impact_analyzer.py**
  - `core.cognition.cognition_graph`

**core/cognition/pattern_extractor.py**
  - `core.observability.logger`
  - `core.storage.storage_manager`

**core/cognition/risk_predictor.py**
  - `core.cognition.cognition_graph`
  - `core.cognition.cognition_models`

**core/cognition/topology_engine.py**
  - `core.cognition.cognition_graph`
  - `core.cognition.cognition_models`

**core/connectors/obsidian_connector.py**
  - `core.observability.logger`

**core/development/architecture_validator.py**
  - `core.development.development_models`

**core/development/branch_execution.py**
  - `core.observability.logger`

**core/development/code_generation.py**
  - `core.development.development_models`

**core/development/development_engine.py**
  - `core.development.development_memory`
  - `core.development.execution_fabric`
  - `core.development.feature_planner`
  - `core.development.implementation_engine`
  - `core.development.validation_engine`
  - `core.observability.logger`

**core/development/development_memory.py**
  - `core.storage.storage_manager`

**core/development/development_snapshot.py**
  - `core.development.development_models`

**core/development/execution_fabric.py**
  - `core.observability.logger`

**core/development/feature_planner.py**
  - `core.development.development_models`

**core/development/implementation_engine.py**
  - `core.development.development_models`
  - `core.observability.logger`

**core/development/integration_engine.py**
  - `core.observability.logger`

**core/development/merge_preparation.py**
  - `core.development.development_models`

**core/development/refactor_engine.py**
  - `core.development.development_models`

**core/development/repair_execution.py**
  - `core.observability.logger`

**core/development/test_orchestrator.py**
  - `core.observability.logger`

**core/development/validation_engine.py**
  - `core.development.development_models`

**core/distributed/node_manager.py**
  - `core.distributed.node_registry`

**core/ecosystem/ecosystem_lifecycle.py**
  - `core.ecosystem.ecosystem_models`
  - `core.ecosystem.ecosystem_registry`

**core/ecosystem/ecosystem_materializer.py**
  - `core.ecosystem.ecosystem_registry`
  - `core.ecosystem.ecosystem_validator`
  - `core.observability.logger`

**core/ecosystem/ecosystem_registry.py**
  - `core.ecosystem.ecosystem_materializer`
  - `core.ecosystem.ecosystem_models`
  - `core.observability.logger`
  - `core.storage.storage_manager`

**core/ecosystem/ecosystem_validator.py**
  - `core.ecosystem.ecosystem_registry`
  - `core.observability.logger`

**core/ecosystem/reality_sync_engine.py**
  - `core.ecosystem.ecosystem_models`
  - `core.ecosystem.ecosystem_registry`
  - `core.observability.logger`
  - `core.storage.storage_manager`

**core/ecosystem/safe_import_system.py**
  - `core.ecosystem.ecosystem_models`
  - `core.ecosystem.ecosystem_registry`
  - `core.observability.logger`

**core/event_bus/event_bus.py**
  - `core.observability.event_stream`
  - `core.observability.logger`
  - `core.storage.event_store`
  - `core.validation.event_validator`

**core/evolution/evolution_engine.py**
  - `core.evolution.regeneration_models`
  - `core.observability.logger`

**core/execution/execution_engine.py**
  - `core.execution.branch_manager`
  - `core.execution.worktree_manager`

**core/execution/git_utils.py**
  - `core.observability.logger`

**core/execution/worktree_manager.py**
  - `core.execution.git_utils`
  - `core.observability.logger`

**core/execution_fabric/autonomous_executor.py**
  - `core.execution.approval_manager`
  - `core.execution_fabric.execution_supervisor`
  - `core.execution_fabric.safe_patch_engine`
  - `core.execution_fabric.worktree_runtime`
  - `core.observability.logger`

**core/execution_fabric/branch_orchestrator.py**
  - `core.execution.git_utils`
  - `core.observability.logger`

**core/execution_fabric/execution_cycles.py**
  - `core.execution_fabric.autonomous_executor`
  - `core.observability.logger`

**core/execution_fabric/execution_fabric.py**
  - `core.execution_fabric.execution_cycles`
  - `core.execution_fabric.execution_memory`
  - `core.execution_fabric.execution_supervisor`
  - `core.execution_fabric.task_dispatcher`

**core/execution_fabric/execution_memory.py**
  - `core.observability.logger`

**core/execution_fabric/execution_recovery.py**
  - `core.observability.logger`

**core/execution_fabric/execution_supervisor.py**
  - `core.execution.approval_manager`
  - `core.observability.logger`

**core/execution_fabric/safe_patch_engine.py**
  - `core.observability.logger`

**core/execution_fabric/task_dispatcher.py**
  - `core.execution_fabric.autonomous_executor`
  - `core.observability.logger`

**core/execution_fabric/validation_pipeline.py**
  - `core.observability.logger`

**core/execution_fabric/worktree_runtime.py**
  - `core.observability.logger`

**core/fabric/resource_fabric.py**
  - `core.fabric.resource_models`
  - `core.observability.logger`

**core/federation/convergence_analyzer.py**
  - `core.observability.logger`

**core/federation/ecosystem_registry.py**
  - `core.federation.federation_models`

**core/federation/federation_engine.py**
  - `core.federation.ecosystem_registry`
  - `core.federation.federation_governance`
  - `core.federation.federation_models`
  - `core.federation.federation_routing`
  - `core.observability.logger`

**core/federation/federation_governance.py**
  - `core.federation.federation_models`

**core/federation/federation_memory.py**
  - `core.storage.storage_manager`

**core/federation/federation_routing.py**
  - `core.federation.federation_models`

**core/federation/federation_snapshot.py**
  - `core.federation.federation_models`

**core/federation/node_registry.py**
  - `core.federation.node_identity`
  - `core.observability.logger`

**core/governance/deadlock_detector.py**
  - `core.observability.logger`

**core/governance/degradation_controller.py**
  - `core.governance.governance_models`
  - `core.observability.logger`

**core/governance/event_governor.py**
  - `core.governance.runtime_limits`
  - `core.observability.logger`

**core/governance/execution_governor.py**
  - `core.observability.logger`
  - `core.storage.storage_manager`

**core/governance/execution_throttler.py**
  - `core.observability.logger`

**core/governance/governance_engine.py**
  - `core.governance.deadlock_detector`
  - `core.governance.degradation_controller`
  - `core.governance.event_governor`
  - `core.governance.execution_throttler`
  - `core.governance.loop_detector`
  - `core.governance.memory_controller`
  - `core.governance.provider_rate_control`
  - `core.governance.queue_balancer`
  - `core.governance.recursion_guard`
  - `core.governance.resource_monitor`
  - `core.governance.runtime_limits`
  - `core.governance.self_modification_guard`
  - `core.governance.storm_protection`
  - `core.governance.workload_scheduler`
  - `core.observability.logger`
  - `core.runtime.runtime_profile`

**core/governance/loop_detector.py**
  - `core.observability.logger`

**core/governance/memory_controller.py**
  - `core.governance.governance_models`
  - `core.observability.logger`

**core/governance/provider_rate_control.py**
  - `core.observability.logger`

**core/governance/recursion_guard.py**
  - `core.observability.logger`

**core/governance/resource_governor.py**
  - `core.observability.logger`

**core/governance/resource_monitor.py**
  - `core.governance.governance_models`
  - `core.observability.logger`

**core/governance/self_modification_guard.py**
  - `core.observability.logger`

**core/governance/storm_protection.py**
  - `core.observability.logger`

**core/governance/workload_scheduler.py**
  - `core.observability.logger`

**core/import_fabric/adapter_generator.py**
  - `core.observability.logger`

**core/import_fabric/dependency_mapper.py**
  - `core.repository_intelligence.tech_detector`

**core/import_fabric/duplication_engine.py**
  - `core.repository_intelligence.duplicate_detector`

**core/import_fabric/import_orchestrator.py**
  - `core.import_fabric.dependency_mapper`
  - `core.import_fabric.external_registry`
  - `core.import_fabric.repo_classifier`
  - `core.import_fabric.repo_cloner`
  - `core.import_fabric.repo_health`
  - `core.import_fabric.repo_indexer`
  - `core.observability.logger`

**core/import_fabric/repo_classifier.py**
  - `core.repository_intelligence.repo_classifier`
  - `core.repository_intelligence.tech_detector`

**core/import_fabric/repo_cloner.py**
  - `core.execution.git_utils`
  - `core.observability.logger`

**core/import_fabric/upstream_tracker.py**
  - `core.execution.git_utils`

**core/kernel/cognitive_kernel.py**
  - `core.federation.ecosystem_registry`
  - `core.kernel.execution_context`
  - `core.kernel.kernel_models`
  - `core.observability.logger`

**core/kernel/execution_context.py**
  - `core.kernel.kernel_models`
  - `core.observability.logger`

**core/kernel/kernel_models.py**
  - `core.federation.federation_models`

**core/kernel/live_kernel.py**
  - `core.observability.logger`
  - `core.operator.autonomous_operator`
  - `core.repository_intelligence.intelligence_engine`
  - `core.repository_intelligence.repo_importer`
  - `core.strategy.goal_engine`

**core/knowledge/concept_extractor.py**
  - `core.observability.logger`

**core/knowledge/context_linker.py**
  - `core.knowledge.knowledge_models`
  - `core.observability.logger`

**core/knowledge/knowledge_engine.py**
  - `core.knowledge.concept_extractor`
  - `core.knowledge.context_linker`
  - `core.knowledge.knowledge_models`
  - `core.knowledge.knowledge_query`
  - `core.knowledge.memory_indexer`
  - `core.knowledge.operational_context`
  - `core.knowledge.relationship_inference`
  - `core.knowledge.semantic_graph`
  - `core.knowledge.semantic_memory`
  - `core.knowledge.semantic_search`
  - `core.knowledge.temporal_memory`
  - `core.observability.logger`

**core/knowledge/knowledge_query.py**
  - `core.knowledge.knowledge_models`
  - `core.knowledge.semantic_graph`

**core/knowledge/memory_indexer.py**
  - `core.knowledge.knowledge_models`
  - `core.observability.logger`

**core/knowledge/operational_context.py**
  - `core.knowledge.knowledge_models`
  - `core.observability.logger`

**core/knowledge/relationship_inference.py**
  - `core.knowledge.knowledge_models`
  - `core.observability.logger`

**core/knowledge/semantic_graph.py**
  - `core.knowledge.knowledge_models`
  - `core.observability.logger`

**core/knowledge/semantic_memory.py**
  - `core.knowledge.knowledge_models`
  - `core.observability.logger`
  - `core.storage.storage_manager`

**core/knowledge/semantic_search.py**
  - `core.knowledge.knowledge_models`
  - `core.knowledge.memory_indexer`
  - `core.observability.logger`

**core/knowledge/temporal_memory.py**
  - `core.knowledge.knowledge_models`

**core/knowledge_graph/graph_store.py**
  - `core.observability.logger`

**core/knowledge_graph/memory_consolidator.py**
  - `core.knowledge_graph.graph_store`
  - `core.memory.consolidation_engine`
  - `core.observability.logger`

**core/knowledge_graph/semantic_linker.py**
  - `core.observability.logger`

**core/lifecycle/bootstrap.py**
  - `core.storage.init_db`
  - `core.storage.storage_manager`

**core/local_runtime/local_executor.py**
  - `core.observability.logger`

**core/local_runtime/local_task_queue.py**
  - `core.autonomy.scheduler.task_queue`

**core/local_runtime/process_supervisor.py**
  - `core.observability.logger`

**core/local_runtime/runtime_watchdog.py**
  - `core.runtime_daemon.watchdog`

**core/memory/code_evolution_memory.py**
  - `core.observability.logger`
  - `core.storage.storage_manager`

**core/memory/consolidation_engine.py**
  - `core.observability.logger`
  - `core.storage.storage_manager`

**core/memory/context_snapshot.py**
  - `core.memory.memory_store`
  - `core.memory.models`

**core/memory/memory_engine.py**
  - `core.observability.logger`
  - `core.storage.storage_manager`

**core/memory/memory_manager.py**
  - `core.memory.memory_engine`
  - `core.memory.memory_store`

**core/memory/memory_store.py**
  - `core.memory.models`
  - `core.storage.storage_manager`

**core/memory/project_families.py**
  - `core.memory.repo_similarity`
  - `core.repository_intelligence.models`

**core/memory/relationship_engine.py**
  - `core.observability.logger`

**core/model_router/fallback_router.py**
  - `core.observability.logger`

**core/model_router/inference_dispatcher.py**
  - `core.observability.logger`

**core/model_router/local_provider_adapter.py**
  - `core.observability.logger`

**core/model_router/model_health.py**
  - `core.observability.logger`

**core/model_router/model_registry.py**
  - `core.observability.logger`

**core/model_router/routing_engine.py**
  - `core.model_router.model_registry`
  - `core.observability.logger`

**core/observability/event_stream.py**
  - `core.realtime.realtime_broadcast`

**core/observability/execution_journal.py**
  - `core.observability.logger`
  - `core.storage.storage_manager`

**core/observability/runtime_metrics.py**
  - `core.observability.logger`
  - `core.storage.storage_manager`

**core/operator/autonomous_operator.py**
  - `core.observability.logger`
  - `core.operator.autonomous_scheduler`
  - `core.operator.task_daemon`

**core/operator/autonomous_scheduler.py**
  - `core.observability.logger`

**core/operator/background_runtime.py**
  - `core.observability.logger`
  - `core.operator.autonomous_operator`
  - `core.operator.task_daemon`

**core/operator/capability_extractor.py**
  - `core.observability.logger`

**core/operator/conversation_indexer.py**
  - `core.provider_sync.conversation_indexer`

**core/operator/execution_supervisor.py**
  - `core.observability.logger`

**core/operator/project_classifier.py**
  - `core.repository_intelligence.repo_classifier`

**core/operator/provider_sync.py**
  - `core.provider_sync.provider_memory_sync`

**core/operator/repo_consolidator.py**
  - `core.observability.logger`

**core/operator/self_improvement_loop.py**
  - `core.autonomous_dev.technical_debt_engine`
  - `core.observability.logger`

**core/operator/task_daemon.py**
  - `core.autonomy.task_queue`
  - `core.observability.logger`

**core/overseer/overseer.py**
  - `core.observability.logger`

**core/planning/capability_gap_detector.py**
  - `core.observability.logger`

**core/planning/dependency_planner.py**
  - `core.observability.logger`

**core/planning/milestone_tracker.py**
  - `core.observability.logger`
  - `core.planning.roadmap_engine`

**core/planning/roadmap_engine.py**
  - `core.observability.logger`
  - `core.storage.storage_manager`

**core/planning/strategic_memory.py**
  - `core.observability.logger`
  - `core.storage.storage_manager`

**core/provider_memory/project_manager.py**
  - `core.observability.logger`
  - `core.storage.storage_manager`

**core/provider_memory/relationship_manager.py**
  - `core.observability.logger`
  - `core.provider_memory.models`
  - `core.provider_memory.project_manager`

**core/provider_mesh/capability_router.py**
  - `core.observability.logger`
  - `core.provider_mesh.provider_ranker`

**core/provider_mesh/consensus_engine.py**
  - `core.observability.logger`

**core/provider_mesh/disagreement_detector.py**
  - `core.observability.logger`

**core/provider_mesh/latency_router.py**
  - `core.observability.logger`

**core/provider_mesh/provider_orchestrator.py**
  - `core.observability.logger`
  - `core.provider_mesh.consensus_engine`
  - `core.provider_mesh.provider_ranker`
  - `core.provider_sync.provider_registry`

**core/provider_mesh/provider_ranker.py**
  - `core.observability.logger`
  - `core.provider_sync.provider_registry`

**core/provider_mesh/synthesis_engine.py**
  - `core.observability.logger`

**core/provider_sync/provider_memory_sync.py**
  - `core.observability.logger`
  - `core.operator.provider_sync`
  - `core.provider_sync.provider_health`

**core/provider_sync/provider_registry.py**
  - `core.observability.logger`
  - `core.providers.base.provider_base`
  - `core.storage.storage_manager`

**core/provider_sync/sync_engine.py**
  - `core.observability.logger`
  - `core.providers.base.provider_base`

**core/providers/base/provider_base.py**
  - `core.realtime.realtime_broadcast`
  - `core.security.vault`

**core/providers/browser/recovery_connectors.py**
  - `core.observability.logger`
  - `core.providers.browser.browser_manager`
  - `core.security.vault`

**core/providers/chatgpt/chatgpt_provider.py**
  - `core.observability.logger`
  - `core.providers.base.provider_base`
  - `core.providers.browser.browser_manager`

**core/providers/claude/claude_provider.py**
  - `core.observability.logger`
  - `core.providers.base.provider_base`

**core/providers/conversation_classifier.py**
  - `core.providers.models.conversation`

**core/providers/conversation_memory.py**
  - `core.memory.memory_store`
  - `core.memory.models`
  - `core.providers.models.conversation`

**core/providers/conversation_sync/ingestion_engine.py**
  - `core.autonomy.task_generator`
  - `core.observability.logger`

**core/providers/custom/custom_provider.py**
  - `core.observability.logger`
  - `core.providers.base.provider_base`

**core/providers/deepseek/deepseek_provider.py**
  - `core.observability.logger`
  - `core.providers.base.provider_base`

**core/providers/gemini/gemini_provider.py**
  - `core.observability.logger`
  - `core.providers.base.provider_base`

**core/providers/grok/grok_provider.py**
  - `core.observability.logger`
  - `core.providers.base.provider_base`

**core/providers/knowledge_normalizer.py**
  - `core.observability.logger`
  - `core.providers.models.conversation`
  - `core.storage.storage_manager`

**core/providers/local_ai_fabric/ollama_adapter.py**
  - `core.observability.logger`

**core/providers/local_ai_fabric/provider_factory.py**
  - `core.observability.logger`

**core/providers/model_router.py**
  - `core.observability.logger`

**core/providers/ollama/ollama_provider.py**
  - `core.observability.logger`
  - `core.providers.base.provider_base`

**core/providers/openai/openai_provider.py**
  - `core.observability.logger`
  - `core.providers.base.provider_base`

**core/providers/openrouter/openrouter_provider.py**
  - `core.observability.logger`
  - `core.providers.base.provider_base`

**core/providers/openwebui/openwebui_provider.py**
  - `core.observability.logger`
  - `core.providers.base.provider_base`

**core/providers/performance/health_monitor.py**
  - `core.observability.logger`
  - `core.provider_sync.provider_registry`
  - `core.realtime.realtime_broadcast`

**core/providers/performance/provider_affinity_engine.py**
  - `core.observability.logger`

**core/providers/performance/provider_benchmark.py**
  - `core.observability.logger`

**core/providers/performance/provider_cost_optimizer.py**
  - `core.observability.logger`

**core/providers/performance/provider_routing_engine.py**
  - `core.observability.logger`
  - `core.providers.base.provider_base`
  - `core.providers.performance.provider_capability_matrix`

**core/providers/performance/provider_scoring.py**
  - `core.observability.logger`

**core/providers/poisongpt/poisongpt_provider.py**
  - `core.observability.logger`
  - `core.providers.base.provider_base`

**core/providers/provider_registry.py**
  - `core.provider_sync.provider_registry`

**core/providers/provider_runtime.py**
  - `core.observability.logger`
  - `core.provider_sync.provider_registry`

**core/providers/proxima/proxima_bridge.py**
  - `core.observability.logger`
  - `core.providers.base.provider_base`

**core/providers/qwen/qwen_provider.py**
  - `core.observability.logger`
  - `core.providers.base.provider_base`

**core/providers/session/session_manager.py**
  - `core.storage.storage_manager`

**core/providers/z/z_provider.py**
  - `core.observability.logger`
  - `core.providers.base.provider_base`

**core/realtime/realtime_broadcast.py**
  - `core.observability.logger`
  - `core.realtime.websocket_manager`

**core/recovery/crash_classifier.py**
  - `core.recovery.recovery_models`

**core/recovery/degradation_manager.py**
  - `core.observability.logger`

**core/recovery/health_monitor.py**
  - `core.observability.logger`
  - `core.recovery.recovery_models`

**core/recovery/isolation_engine.py**
  - `core.observability.logger`

**core/recovery/memory_recovery.py**
  - `core.observability.logger`

**core/recovery/node_recovery.py**
  - `core.observability.logger`

**core/recovery/orchestration_recovery.py**
  - `core.observability.logger`

**core/recovery/provider_recovery.py**
  - `core.observability.logger`

**core/recovery/recovery_engine.py**
  - `core.observability.logger`
  - `core.recovery.crash_classifier`
  - `core.recovery.health_monitor`
  - `core.recovery.isolation_engine`
  - `core.recovery.provider_recovery`
  - `core.recovery.recovery_memory`
  - `core.recovery.repair_chain`
  - `core.recovery.runtime_recovery`

**core/recovery/recovery_memory.py**
  - `core.storage.storage_manager`

**core/recovery/recovery_snapshot.py**
  - `core.recovery.recovery_models`

**core/recovery/repair_chain.py**
  - `core.observability.logger`

**core/recovery/rollback_recovery.py**
  - `core.observability.logger`

**core/recovery/runtime_recovery.py**
  - `core.observability.logger`

**core/recovery/service_restarter.py**
  - `core.observability.logger`

**core/recovery/state_rebuilder.py**
  - `core.observability.logger`

**core/repository_cognition/architecture_mapper.py**
  - `core.observability.logger`

**core/repository_cognition/repo_scanner.py**
  - `core.observability.logger`

**core/repository_cognition/repository_civilizer.py**
  - `core.observability.logger`

**core/repository_intelligence/duplicate_detector.py**
  - `core.repository_intelligence.models`

**core/repository_intelligence/intelligence_engine.py**
  - `core.ecosystem.ecosystem_models`
  - `core.ecosystem.ecosystem_registry`
  - `core.observability.logger`
  - `core.repository_intelligence.external_repos`

**core/repository_intelligence/operational_feed.py**
  - `core.autonomy.models`
  - `core.observability.logger`
  - `core.realtime.realtime_broadcast`

**core/repository_intelligence/repo_federation.py**
  - `core.ecosystem.ecosystem_models`
  - `core.ecosystem.ecosystem_registry`
  - `core.observability.logger`
  - `core.storage.storage_manager`

**core/repository_intelligence/repo_graph.py**
  - `core.repository_intelligence.models`

**core/repository_intelligence/repo_importer.py**
  - `core.ecosystem.ecosystem_models`
  - `core.ecosystem.ecosystem_registry`
  - `core.execution.git_utils`
  - `core.observability.logger`
  - `core.repository_intelligence.github_client`
  - `core.repository_intelligence.repo_classifier`
  - `core.repository_intelligence.tech_detector`

**core/repository_intelligence/repo_watchers.py**
  - `core.observability.logger`

**core/repository_intelligence/scanner.py**
  - `core.observability.logger`
  - `core.repository_intelligence.models`
  - `core.repository_intelligence.repo_classifier`
  - `core.repository_intelligence.tech_detector`

**core/research/experiment_memory.py**
  - `core.storage.storage_manager`

**core/research/experiment_snapshot.py**
  - `core.research.research_models`

**core/research/experimentation_engine.py**
  - `core.research.research_models`

**core/research/isolation_controller.py**
  - `core.observability.logger`

**core/research/provider_benchmarking.py**
  - `core.research.benchmark_models`

**core/research/research_engine.py**
  - `core.observability.logger`
  - `core.research.experimentation_engine`
  - `core.research.isolation_controller`
  - `core.research.research_models`
  - `core.research.sandbox_runtime`

**core/research/sandbox_runtime.py**
  - `core.observability.logger`
  - `core.research.research_models`

**core/runtime/health_score.py**
  - `core.observability.logger`

**core/runtime/reality_snapshot.py**
  - `core.ecosystem.ecosystem_registry`
  - `core.observability.logger`
  - `core.provider_sync.provider_registry`
  - `core.runtime.runtime_path_validator`
  - `core.runtime.runtime_profile`
  - `core.runtime.safe_action_queue`

**core/runtime/runtime.py**
  - `core.agents.autonomy_agent`
  - `core.agents.provider_agent`
  - `core.agents.repo_agent`
  - `core.api.api_server`
  - `core.event_bus.event_bus`
  - `core.observability.logger`
  - `core.overseer.overseer`
  - `core.runtime.health_score`
  - `core.runtime.reality_snapshot`
  - `core.runtime.runtime_profile`
  - `core.runtime.runtime_state_broadcast`
  - `core.runtime.runtime_state_store`
  - `core.runtime.safe_action_queue`
  - `core.runtime_state.runtime_state`

**core/runtime/runtime_path_validator.py**
  - `core.observability.logger`

**core/runtime/runtime_profile.py**
  - `core.observability.logger`

**core/runtime/runtime_state_broadcast.py**
  - `core.realtime.realtime_broadcast`
  - `core.runtime.runtime_state_store`

**core/runtime/runtime_state_store.py**
  - `core.observability.logger`

**core/runtime/safe_action_queue.py**
  - `core.observability.logger`
  - `core.storage.database`
  - `core.storage.init_db`
  - `core.storage.models`

**core/runtime_daemon/daemon.py**
  - `core.observability.logger`
  - `core.runtime_daemon.heartbeat`
  - `core.runtime_daemon.process_registry`
  - `core.runtime_daemon.supervisor`
  - `core.runtime_daemon.watchdog`

**core/runtime_daemon/heartbeat.py**
  - `core.observability.logger`
  - `core.runtime.runtime_state_store`

**core/runtime_daemon/process_registry.py**
  - `core.observability.logger`

**core/runtime_daemon/supervisor.py**
  - `core.observability.logger`

**core/runtime_daemon/watchdog.py**
  - `core.observability.logger`
  - `core.runtime_daemon.heartbeat`

**core/sandbox/execution_journal.py**
  - `core.observability.logger`

**core/sandbox/execution_limits.py**
  - `core.observability.logger`

**core/sandbox/isolated_runtime.py**
  - `core.execution_fabric.worktree_runtime`
  - `core.observability.logger`
  - `core.sandbox.execution_limits`

**core/sandbox/rollback_runtime.py**
  - `core.observability.logger`

**core/sandbox/runtime_replay.py**
  - `core.observability.logger`

**core/sandbox/snapshot_manager.py**
  - `core.observability.logger`

**core/search/internal_search_engine.py**
  - `core.observability.logger`
  - `core.storage.storage_manager`

**core/security/vault.py**
  - `core.observability.logger`
  - `core.storage.storage_manager`

**core/self_evolution/architecture_optimizer.py**
  - `core.observability.logger`

**core/self_evolution/autonomous_refactorer.py**
  - `core.observability.logger`

**core/self_evolution/benchmark_engine.py**
  - `core.observability.logger`

**core/self_evolution/capability_expander.py**
  - `core.observability.logger`

**core/self_evolution/evolution_engine.py**
  - `core.observability.logger`
  - `core.self_evolution.patch_candidate_generator`
  - `core.self_evolution.safety_validator`
  - `core.self_evolution.sandbox_runner`

**core/self_evolution/evolution_guardrails.py**
  - `core.observability.logger`

**core/self_evolution/evolution_memory.py**
  - `core.observability.logger`
  - `core.storage.storage_manager`

**core/self_evolution/patch_generator.py**
  - `core.observability.logger`

**core/self_evolution/promotion_engine.py**
  - `core.observability.logger`

**core/self_evolution/regression_guard.py**
  - `core.observability.logger`

**core/self_evolution/rollback_manager.py**
  - `core.observability.logger`

**core/self_evolution/safety_validator.py**
  - `core.observability.logger`

**core/self_evolution/sandbox_runner.py**
  - `core.observability.logger`

**core/self_evolution/self_analysis_engine.py**
  - `core.observability.logger`

**core/self_healing/degraded_mode_router.py**
  - `core.observability.logger`

**core/storage/event_store.py**
  - `core.observability.logger`
  - `core.storage.database`
  - `core.storage.init_db`
  - `core.storage.models`

**core/storage/init_db.py**
  - `core.observability.logger`
  - `core.storage.database`
  - `core.storage.models`

**core/storage/models.py**
  - `core.storage.database`

**core/storage/storage_manager.py**
  - `core.observability.logger`

**core/strategy/debt_predictor.py**
  - `core.strategy.roadmap_models`

**core/strategy/ecosystem_planner.py**
  - `core.federation.ecosystem_registry`
  - `core.federation.federation_models`

**core/strategy/goal_engine.py**
  - `core.ecosystem.ecosystem_models`
  - `core.observability.logger`
  - `core.repository_intelligence.repo_importer`

**core/strategy/priority_engine.py**
  - `core.strategy.roadmap_models`

**core/strategy/roadmap_engine.py**
  - `core.strategy.roadmap_models`

**core/strategy/strategic_memory.py**
  - `core.storage.storage_manager`

**core/strategy/strategy_engine.py**
  - `core.observability.logger`
  - `core.strategy.debt_predictor`
  - `core.strategy.priority_engine`
  - `core.strategy.roadmap_engine`
  - `core.strategy.strategy_snapshot`
  - `core.strategy.sustainability_engine`

**core/strategy/strategy_snapshot.py**
  - `core.strategy.roadmap_models`

**core/telemetry/anomaly_metrics.py**
  - `core.observability.logger`

**core/telemetry/metrics_collector.py**
  - `core.observability.logger`
  - `core.storage.storage_manager`

**core/telemetry/runtime_profiler.py**
  - `core.observability.logger`

**core/update/update_engine.py**
  - `core.observability.logger`

**core/workspace/__init__.py**
  - `core.workspace.workspace_manager`

**core/workspace/cognitive_filesystem.py**
  - `core.observability.logger`

**core/workspace/workspace_engine.py**
  - `core.observability.logger`
  - `core.workspace.project_identity`
  - `core.workspace.semantic_project_mapper`
  - `core.workspace.workspace_graph`

**core/workspace/workspace_manager.py**
  - `core.observability.logger`

**force_approve.py**
  - `core.runtime.safe_action_queue`

**legacy/core/agents/base.py**
  - `core.event_bus.bus`

**legacy/core/agents/memory_sync_agent.py**
  - `core.agents.base`
  - `core.event_bus.bus`
  - `core.memory.engine`
  - `core.memory.sync`

**legacy/core/agents/overseer_agent.py**
  - `core.agents.base`
  - `core.event_bus.bus`

**legacy/core/agents/prompt_intelligence_agent.py**
  - `core.agents.base`
  - `core.event_bus.bus`
  - `core.prompt_intelligence.generator`

**legacy/core/agents/provider_connector_agent.py**
  - `core.agents.base`
  - `core.event_bus.bus`

**legacy/core/agents/repo_intelligence_agent.py**
  - `core.agents.base`
  - `core.event_bus.bus`

**legacy/core/agents/validation_agent.py**
  - `core.agents.base`
  - `core.event_bus.bus`

**legacy/core/cockpit/interface.py**
  - `core.event_bus.bus`

**legacy/core/deployment/manager.py**
  - `core.event_bus.bus`

**legacy/core/ecosystem_state/manager.py**
  - `core.event_bus.bus`

**legacy/core/gap_detection/detector.py**
  - `core.event_bus.bus`

**legacy/core/git_engine/git_manager.py**
  - `core.event_bus.bus`

**legacy/core/health/calculator.py**
  - `core.event_bus.bus`

**legacy/core/knowledge_integration/processor.py**
  - `core.event_bus.bus`
  - `core.memory.engine`

**legacy/core/memory/sync.py**
  - `core.event_bus.bus`

**legacy/core/meta_reasoning/orchestrator.py**
  - `core.event_bus.bus`

**legacy/core/observability/logger.py**
  - `core.event_bus.bus`

**legacy/core/observability/metrics.py**
  - `core.event_bus.bus`

**legacy/core/overseer/overseer.py**
  - `core.event_bus.bus`

**legacy/core/prompt_library/genome.py**
  - `core.memory.engine`

**legacy/core/repository_intelligence/auto_repair.py**
  - `core.event_bus.bus`
  - `core.git_engine.git_manager`

**legacy/core/self_healing/engine.py**
  - `core.event_bus.bus`

**legacy/core/validation/drift.py**
  - `core.event_bus.bus`

**legacy/core/validation/engine.py**
  - `core.event_bus.bus`

**legacy/tests/test_drift.py**
  - `core.event_bus.bus`
  - `core.observability.logger`
  - `core.validation.drift`

**legacy/tests/test_phase6.py**
  - `core.cockpit.interface`
  - `core.deployment.manager`
  - `core.ecosystem_state.manager`
  - `core.event_bus.bus`
  - `core.git_engine.git_manager`
  - `core.health.calculator`
  - `core.memory.sync`
  - `core.overseer.overseer`
  - `core.repository_intelligence.auto_repair`
  - `core.self_healing.engine`

**legacy/tests/test_phase7.py**
  - `core.agents.base`
  - `core.agents.prompt_intelligence_agent`
  - `core.agents.provider_connector_agent`
  - `core.ecosystem_state.manager`
  - `core.event_bus.bus`
  - `core.gap_detection.detector`
  - `core.knowledge_integration.processor`
  - `core.memory.engine`
  - `core.meta_reasoning.orchestrator`

**legacy/tests/test_system.py**
  - `core.agents.base`
  - `core.event_bus.bus`
  - `core.observability.logger`
  - `core.overseer.overseer`
  - `core.validation.drift`
  - `core.validation.engine`

**main.py**
  - `core.bootstrap`
  - `core.observability.logger`
  - `core.runtime.runtime`

**scripts/autonomous_dry_run.py**
  - `core.autonomy.active_runtime.cognition_loop`
  - `core.observability.logger`

**scripts/autostart/autonomous_loop.py**
  - `scripts.autostart.start_daemon`

**scripts/autostart/boot_runtime.py**
  - `core.lifecycle.bootstrap_engine`
  - `core.observability.logger`

**scripts/autostart/recovery_monitor.py**
  - `core.observability.logger`

**scripts/autostart/restore_sessions.py**
  - `core.autonomy.mission_engine`
  - `core.observability.logger`
  - `core.storage.storage_manager`

**scripts/autostart/start_cockpit.py**
  - `core.observability.logger`

**scripts/autostart/start_daemon.py**
  - `core.autonomy.active_runtime.cognition_loop`
  - `core.observability.logger`

**scripts/autostart/start_runtime.py**
  - `core.observability.logger`

**scripts/autostart/worker_cluster.py**
  - `core.agents.base_agent`
  - `core.observability.logger`

**scripts/bootstrap_tests/test_bootstrap_logic.py**
  - `core.bootstrap`
  - `core.storage.storage_manager`

**scripts/executable_runtime_test.py**
  - `core.observability.logger`

**scripts/extract_repo.py**
  - `core.autonomous_dev.repository_extractor`

**scripts/fase_43_6_force_cognition.py**
  - `core.autonomy.active_runtime.cognition_loop`
  - `core.autonomy.mission_engine`
  - `core.observability.logger`
  - `core.runtime.safe_action_queue`

**scripts/fase_43_6_force_cognition_real.py**
  - `core.autonomy.active_runtime.cognition_loop`
  - `core.autonomy.mission_engine`
  - `core.runtime.safe_action_queue`

**scripts/phase35_imports.py**
  - `core.observability.logger`
  - `core.repository_intelligence.repo_importer`

**scripts/phase_finalizer.py**
  - `core.federation.ecosystem_registry`
  - `core.kernel.cognitive_kernel`
  - `core.storage.storage_manager`
  - `core.strategy.strategic_memory`

**scripts/runtime_smoke_test.py**
  - `core.bootstrap`
  - `core.observability.logger`
  - `core.runtime.runtime`
  - `core.storage.storage_manager`

**scripts/stress_test_memory.py**
  - `core.memory.consolidation_engine`
  - `core.memory.memory_engine`
  - `core.observability.logger`

**scripts/stress_test_providers.py**
  - `core.observability.logger`
  - `core.providers.chatgpt.chatgpt_provider`
  - `core.providers.claude.claude_provider`
  - `core.providers.performance.provider_routing_engine`

**scripts/validate_executable.py**
  - `core.observability.logger`

**scripts/verify_cockpit_persistence.py**
  - `core.storage.storage_manager`

**scripts/verify_mission_recovery.py**
  - `core.autonomy.mission_engine`
  - `core.autonomy.mission_models`
  - `core.observability.logger`

**shared/config/settings.py**
  - `core.storage.storage_manager`

**tests/autonomous_dev/test_repository_extractor.py**
  - `core.autonomous_dev.repository_extractor`

**tests/autonomy/test_analysis.py**
  - `core.autonomy.repo_analysis_pipeline`

**tests/autonomy/test_continuous_runtime.py**
  - `core.autonomy.continuous_runtime.cognition_scheduler`
  - `core.autonomy.continuous_runtime.runtime_core`

**tests/autonomy/test_degraded_mode.py**
  - `core.self_healing.degraded_mode_router`

**tests/autonomy/test_engines.py**
  - `core.autonomy.models`
  - `core.autonomy.priority_engine`
  - `core.autonomy.task_generator`

**tests/autonomy/test_loop.py**
  - `core.autonomy.autonomous_loop`

**tests/autonomy/test_mission_system.py**
  - `core.autonomy.active_runtime.objective_engine`
  - `core.autonomy.mission_engine`
  - `core.autonomy.mission_models`

**tests/autonomy/test_phase37_logic.py**
  - `core.autonomy.active_runtime.cognition_loop`
  - `core.model_router.routing_engine`
  - `core.planning.roadmap_engine`
  - `core.self_evolution.safety_validator`

**tests/autonomy/test_scheduler.py**
  - `core.autonomy.scheduler.task_queue`

**tests/bootstrap/test_bootstrap_logic.py**
  - `core.bootstrap`
  - `core.storage.storage_manager`

**tests/daemon/test_daemon_persistence.py**
  - `core.runtime_daemon.daemon`

**tests/ecosystem/test_protection_rules.py**
  - `core.workspace.workspace_manager`

**tests/ecosystem/test_reality_sync.py**
  - `core.ecosystem.ecosystem_models`
  - `core.ecosystem.ecosystem_registry`
  - `core.ecosystem.reality_sync_engine`

**tests/execution_fabric/test_execution_fabric.py**
  - `core.agents.specialization.specialization_registry`
  - `core.execution_fabric.execution_state_machine`

**tests/execution_fabric/test_execution_logic.py**
  - `core.execution.branch_manager`
  - `core.execution.merge_guard`

**tests/import_fabric/test_import_intelligence_v7.py**
  - `core.kernel.live_kernel`
  - `core.repository_intelligence.intelligence_engine`
  - `core.repository_intelligence.repo_importer`
  - `core.strategy.goal_engine`

**tests/import_fabric/test_phase15_16_17_import.py**
  - `core.distributed.distributed_memory`
  - `core.distributed.mesh_models`
  - `core.distributed.node_capabilities`
  - `core.distributed.node_failover`
  - `core.distributed.node_heartbeat`
  - `core.distributed.node_identity`
  - `core.distributed.node_manager`
  - `core.distributed.node_registry`
  - `core.distributed.node_state`
  - `core.distributed.node_sync`
  - `core.execution.approval_manager`
  - `core.execution.branch_manager`
  - `core.execution.execution_context`
  - `core.execution.execution_engine`
  - `core.execution.execution_models`
  - `core.execution.merge_guard`
  - `core.execution.repair_loop`
  - `core.execution.rollback_engine`
  - `core.execution.worktree_manager`
  - `core.labs.architecture_analyzer`
  - `core.labs.lab_memory`
  - `core.labs.lab_scanner`
  - `core.labs.orchestration_detector`
  - `core.labs.pattern_extractor`
  - `core.learning.adaptive_routing`
  - `core.learning.capability_evolution`
  - `core.learning.execution_learning`
  - `core.learning.failure_learning`
  - `core.learning.learning_engine`
  - `core.learning.learning_models`
  - `core.learning.learning_snapshot`
  - `core.learning.orchestration_learning`
  - `core.learning.pattern_memory`
  - `core.learning.prompt_learning`
  - `core.learning.provider_learning`
  - `core.learning.specialization_engine`

**tests/import_fabric/test_repo_import_validation.py**
  - `core.observability.logger`
  - `core.operator.capability_extractor`
  - `core.workspace.workspace_graph`

**tests/import_fabric/test_repo_importer.py**
  - `core.ecosystem.ecosystem_models`
  - `core.ecosystem.ecosystem_registry`
  - `core.repository_intelligence.repo_classifier`
  - `core.repository_intelligence.repo_importer`

**tests/integration/test_api_endpoints.py**
  - `core.api.api_server`

**tests/integration/test_ecosystem.py**
  - `core.ecosystem.ecosystem_lifecycle`
  - `core.ecosystem.ecosystem_models`
  - `core.ecosystem.ecosystem_registry`
  - `core.storage.storage_manager`

**tests/integration/test_ecosystem_materializer.py**
  - `core.ecosystem.ecosystem_materializer`
  - `core.ecosystem.ecosystem_registry`
  - `core.ecosystem.ecosystem_validator`
  - `core.storage.storage_manager`

**tests/integration/test_federation_layer.py**
  - `core.federation.federation_engine`
  - `core.federation.federation_models`

**tests/integration/test_governance_sim.py**
  - `core.governance.runtime_limits`
  - `core.runtime.runtime`
  - `core.storage.database`
  - `core.storage.models`

**tests/integration/test_knowledge_fabric.py**
  - `core.knowledge.knowledge_models`
  - `core.runtime.runtime`

**tests/integration/test_provider_sync.py**
  - `core.observability.logger`
  - `core.operator.provider_sync`

**tests/integration/test_repository_intelligence.py**
  - `core.repository_intelligence.duplicate_detector`
  - `core.repository_intelligence.models`
  - `core.repository_intelligence.repo_classifier`
  - `core.repository_intelligence.tech_detector`

**tests/integration/test_research_layer.py**
  - `core.research.isolation_controller`
  - `core.research.research_engine`
  - `core.research.research_models`

**tests/integration/test_runtime_truth.py**
  - `core.api.api_server`
  - `core.runtime.runtime_state_store`

**tests/integration/test_storage_architecture.py**
  - `core.storage.storage_manager`

**tests/integration/test_strategic_orchestration.py**
  - `core.strategy.debt_predictor`
  - `core.strategy.roadmap_models`
  - `core.strategy.strategy_engine`

**tests/knowledge_graph/test_consolidation.py**
  - `core.knowledge_graph.graph_store`
  - `core.knowledge_graph.memory_consolidator`

**tests/migration/test_engine.py**
  - `core.migration.migration_engine`

**tests/migration/test_rewriter.py**
  - `core.migration.import_rewriter`

**tests/migration/test_scanner.py**
  - `core.migration.dependency_scanner`

**tests/operational/test_cockpit_mission_trace.py**
  - `core.api.api_server`
  - `core.autonomy.mission_engine`
  - `core.runtime.runtime_state_store`
  - `core.runtime.safe_action_queue`

**tests/operational/test_master_runtime.py**
  - `core.runtime.runtime`

**tests/operational/test_phase37_operational.py**
  - `core.node_runtime.node_identity`
  - `core.telemetry.metrics_collector`

**tests/operational/test_recovery.py**
  - `core.autonomy.continuous_runtime.lifecycle_manager`
  - `core.storage.storage_manager`

**tests/operational/test_work_queue.py**
  - `core.autonomy.work_queue`

**tests/platform/test_cognition_survival.py**
  - `core.cognition.cognitive_analysis_engine`

**tests/platform/test_runtime_restoration.py**
  - `core.runtime.runtime`

**tests/provider_mesh/test_mesh_orchestration.py**
  - `core.provider_mesh.consensus_engine`
  - `core.provider_mesh.provider_ranker`
  - `core.provider_sync.provider_registry`

**tests/provider_sync/test_sync.py**
  - `core.provider_sync.provider_memory_sync`

**tests/repository_cognition/test_civilization.py**
  - `core.repository_cognition.repository_civilizer`

**tests/repository_cognition/test_indexing.py**
  - `core.repository_cognition.architecture_mapper`

**tests/runtime/test_health_breakdown.py**
  - `core.runtime.health_score`

**tests/runtime/test_health_score.py**
  - `core.runtime.health_score`

**tests/runtime/test_reality_diff.py**
  - `core.runtime.reality_diff`

**tests/runtime/test_reality_snapshot.py**
  - `core.runtime.reality_snapshot`

**tests/runtime/test_safe_action_queue.py**
  - `core.runtime.safe_action_queue`

**tests/runtime_daemon/test_daemon.py**
  - `core.runtime_daemon.heartbeat`
  - `core.runtime_daemon.process_registry`

**tests/runtime_daemon/test_recovery.py**
  - `core.runtime_daemon.heartbeat`
  - `core.runtime_daemon.process_registry`

**tests/sandbox/test_sandbox_security.py**
  - `core.sandbox.execution_limits`
  - `core.sandbox.isolated_runtime`

**tests/self_evolution/test_self_analysis.py**
  - `core.self_evolution.architecture_optimizer`
  - `core.self_evolution.self_analysis_engine`

**tests/system/test_repo_scanning.py**
  - `core.repository_cognition.repo_scanner`

**tests/system/test_worktree_execution.py**
  - `core.execution_fabric.worktree_runtime`

**tests/test_phase35_autonomy.py**
  - `core.autonomy.models`
  - `core.autonomy.priority_engine`
  - `core.autonomy.self_improvement_planner`
  - `core.autonomy.task_generator`

**tests/test_phase35_cognition.py**
  - `core.cognition.architecture_graph`
  - `core.cognition.cognitive_analysis_engine`
  - `core.cognition.pattern_extractor`

**tests/test_phase35_governance.py**
  - `core.governance.execution_governor`

**tests/unit/test_operational_stability.py**
  - `core.knowledge.memory_indexer`
  - `core.repository_cognition.repo_scanner`

**tests/unit/test_persistent_paths.py**
  - `core.storage.storage_manager`

**tests/unit/test_provider_orchestration_new.py**
  - `core.provider_mesh.capability_router`
  - `core.provider_mesh.provider_orchestrator`
  - `core.provider_sync.provider_registry`

**tests/unit/test_provider_registry.py**
  - `core.provider_sync.provider_registry`
  - `core.storage.storage_manager`

**tests/unit/test_runtime.py**
  - `core.runtime.runtime`
  - `core.storage.database`
  - `core.storage.event_store`
  - `core.storage.models`
  - `core.validation.event_validator`

**tests/unit/test_vault_security.py**
  - `core.security.vault`

**tools/controlled_import.py**
  - `core.ecosystem.ecosystem_models`
  - `core.ecosystem.ecosystem_registry`
  - `core.observability.logger`
  - `core.repository_intelligence.tech_detector`

**tools/import_engine.py**
  - `core.kernel.live_kernel`
  - `core.observability.logger`
  - `core.repository_intelligence.external_repos`
  - `core.repository_intelligence.intelligence_engine`
  - `core.repository_intelligence.repo_importer`
  - `core.strategy.goal_engine`

**verify_architecture.py**
  - `core.api.api_server`
  - `core.memory.memory_manager`
  - `core.runtime.reality_snapshot`
  - `core.runtime.runtime_state_store`
  - `core.runtime.safe_action_queue`

## Parse errors (1)
- scan.py: invalid non-printable character U+FEFF (<unknown>, line 1)
