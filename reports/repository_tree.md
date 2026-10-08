# DGM-MAT Repository Tree
_Generated: 20260530T191704_

**Total:** 987 files | **Python:** 819

## File types
- `.py`: 819
- `.json`: 69
- `.md`: 54
- `no_ext`: 17
- `.yml`: 12
- `.txt`: 9
- `.sh`: 1
- `.toml`: 1
- `.ini`: 1
- `.log`: 1
- `.spec`: 1
- `.qss`: 1
- `.yaml`: 1

## Full tree
```
DGM-MAT/
  .gitignore
  DGM-MAT_TREE.txt
  LICENSE
  README.md
  apply_fix.sh
  architecture.md
  ecosystem.json
  fix_verify.py
  force_approve.py
  gm.py
  health.json
  inspect_db.py
  main.py
  memory_recording.json
  observe.py
  pm.py
  pyproject.toml
  pytest.ini
  requirements.txt
  scan.py
  t.txt
  test_pyside6.py
  verify_all_phase37_38.py
  verify_architecture.py
  verify_cockpit.py
  verify_cockpit_phase38.py
  verify_widgets.py
  .github/
    workflows/
      autonomy-smoke.yml
      bootstrap-repositories.yml
      build-windows.yml
      ci-core.yml
      ci-integration.yml
      manual-repo-bootstrap.yml
      migration-validation.yml
      release.yml
      repo-analysis.yml
      runtime-validation.yml
      security-scan.yml
      workflow-validation.yml
  .runtime/
    ecosystem_registry.json
    external_registry.json
    runtime_state.json
    runtime_trace.log
    execution_journals/
      journal_test_1_20260525_124710.json
    memory_archive/
      124557_mem1.json
      124557_mem2.json
      mem1.json
      mem2.json
      mem_chatgpt_Build a CLI tool_20260525.json
    provider_memory/
      consolidated_chatgpt_build_a_cli_20260525_124557.json
    tasks/
      task_2012986e.json
      task_334a5dd3.json
      task_6d601313.json
      task_91ae4946.json
      task_9d99d8a5.json
      task_adf95b6d.json
    telemetry/
      telemetry_metric_1779791728.json
      telemetry_metric_1779791854.json
      telemetry_metric_1779792394.json
      telemetry_metric_1779792458.json
      telemetry_metric_1779792672.json
      telemetry_metric_1779792756.json
  build/
    dgm_mat.spec
  cockpit/
    __init__.py
    main_window.py
    realtime_client.py
    app/
      __init__.py
      app_foundation.py
      main.py
      websocket_client.py
    approvals/
      patch_review.py
      patch_review_ui.py
      queue_widget.py
    autonomy/
      monitor_widget.py
    memory/
      inspector_widget.py
    providers/
      login_form.py
      management_widget.py
    streaming/
      realtime_client.py
    styles/
      theme.qss
    widgets/
      activity_stream_widget.py
      agent_widget.py
      architecture_graph_view.py
      autonomous_tasks_widget.py
      autonomy_dashboard.py
      cognitive_dashboard.py
      command_console.py
      dashboard_widget.py
      duplicate_detection_widget.py
      ecosystem_graph_widget.py
      event_stream_widget.py
      execution_feed.py
      execution_queue_widget.py
      federation_widget.py
      governance_widget.py
      health_graph.py
      imported_repos_widget.py
      knowledge_feed_widget.py
      knowledge_graph_widget.py
      learning_dashboard_widget.py
      local_execution_widget.py
      logs_widget.py
      mesh_monitor_widget.py
      mission_widget.py
      operational_dashboard.py
      operational_search_widget.py
      project_families_widget.py
      provider_conversations_widget.py
      research_widget.py
      runtime_health_widget.py
      self_improvement_widget.py
      strategy_widget.py
      tech_debt_dashboard.py
      technical_debt_widget.py
      workspace_graph_widget.py
    workspace/
      chat_widget.py
      cognition_graph.py
      execution_timeline_widget.py
      memory_graph.py
      task_feed_widget.py
  config/
    autonomous_runtime.json
    extraction_manifest.json
    import_targets.json
    nodes.json
    protected_assets.yaml
    runtime_limits.json
  core/
    agents/
      architect_agent.py
      autonomy_agent.py
      base_agent.py
      debug_agent.py
      devops_agent.py
      isolated_runtime.py
      memory_agent.py
      provider_agent.py
      refactor_agent.py
      repo_agent.py
      research_agent.py
      runtime_agent.py
      security_agent.py
      self_improvement_agent.py
      ui_agent.py
      watchdog.py
      specialization/
        __init__.py
        adaptive_specialization.py
        agent_profiler.py
        capability_allocator.py
        execution_roles.py
        provider_affinity.py
        runtime_affinity.py
        skill_distribution.py
        specialization_registry.py
        workload_optimizer.py
    api/
      api_server.py
      mobile_bridge.py
      runtime_api.py
    autonomous_dev/
      __init__.py
      architecture_optimizer.py
      autonomous_dev_engine.py
      cleanup_engine.py
      dead_code_detector.py
      dependency_fixer.py
      issue_detector.py
      merge_planner.py
      repo_refactor_loop.py
      repository_extractor.py
      roadmap_executor.py
      self_patch_engine.py
      task_generator.py
      technical_debt_engine.py
    autonomy/
      autonomous_loop.py
      mission_engine.py
      mission_models.py
      models.py
      priority_engine.py
      repair_suggester.py
      repo_analysis_pipeline.py
      safe_autonomous_executor.py
      self_improvement_planner.py
      task_engine.py
      task_generator.py
      task_planner.py
      task_queue.py
      work_queue.py
      worker_allocator.py
      active_runtime/
        autonomy_cycle.py
        cognition_loop.py
        execution_director.py
        learning_loop.py
        objective_engine.py
        strategic_planner.py
      continuous_runtime/
        adaptive_router.py
        autonomous_director.py
        cognition_scheduler.py
        evolution_engine.py
        execution_coordinator.py
        lifecycle_manager.py
        observation_engine.py
        planning_engine.py
        reflection_engine.py
        runtime_core.py
      scheduler/
        __init__.py
        execution_loop.py
        priority_router.py
        retry_manager.py
        scheduler_engine.py
        task_queue.py
    bootstrap/
      __init__.py
      core/
        __init__.py
        bootstrap_context.py
        bootstrap_storage.py
        dependency_loader.py
        environment_detector.py
      federation/
        __init__.py
      providers/
        __init__.py
      runtime/
        __init__.py
        bootstrap_engine.py
        bootstrap_sequence.py
      ui/
        __init__.py
    cockpit_runtime/
      __init__.py
      autonomy_status_api.py
      cognition_visualizer.py
      execution_dashboard.py
      live_task_feed.py
      realtime_runtime_api.py
      runtime_metrics.py
      telemetry_stream.py
      websocket_runtime.py
    cognition/
      architecture_graph.py
      architecture_memory.py
      cognition_graph.py
      cognition_models.py
      cognition_snapshot.py
      cognitive_analysis_engine.py
      convergence_engine.py
      dependency_mapper.py
      ecosystem_engine.py
      ecosystem_health.py
      fragmentation_detector.py
      impact_analyzer.py
      pattern_extractor.py
      risk_predictor.py
      topology_engine.py
    connectors/
      obsidian_connector.py
      adapters/
        AIClient2API_adapter.py
        gpt4free_adapter.py
    development/
      architecture_validator.py
      branch_execution.py
      code_generation.py
      development_engine.py
      development_memory.py
      development_models.py
      development_snapshot.py
      execution_fabric.py
      feature_planner.py
      implementation_engine.py
      integration_engine.py
      merge_preparation.py
      refactor_engine.py
      repair_execution.py
      test_orchestrator.py
      validation_engine.py
    distributed/
      __init__.py
      distributed_memory.py
      mesh_models.py
      node_capabilities.py
      node_failover.py
      node_heartbeat.py
      node_identity.py
      node_manager.py
      node_registry.py
      node_state.py
      node_sync.py
    ecosystem/
      ecosystem_lifecycle.py
      ecosystem_materializer.py
      ecosystem_models.py
      ecosystem_registry.py
      ecosystem_validator.py
      reality_sync_engine.py
      safe_import_system.py
    event_bus/
      event_bus.py
    evolution/
      abstraction_optimizer.py
      adaptive_patterns.py
      architecture_mutation.py
      convergence_optimizer.py
      degradation_analyzer.py
      evolution_engine.py
      evolution_memory.py
      evolution_snapshot.py
      mutation_simulator.py
      orchestration_optimizer.py
      regeneration_engine.py
      regeneration_models.py
      runtime_regenerator.py
      semantic_refactor.py
      structural_forecaster.py
    execution/
      __init__.py
      approval_manager.py
      branch_manager.py
      execution_context.py
      execution_engine.py
      execution_models.py
      git_utils.py
      merge_guard.py
      repair_loop.py
      rollback_engine.py
      worktree_manager.py
    execution_fabric/
      __init__.py
      autonomous_executor.py
      branch_orchestrator.py
      execution_cycles.py
      execution_fabric.py
      execution_memory.py
      execution_recovery.py
      execution_state_machine.py
      execution_supervisor.py
      safe_patch_engine.py
      task_dispatcher.py
      validation_pipeline.py
      worktree_runtime.py
    fabric/
      cluster_scheduler.py
      cognition_cluster.py
      distributed_storage.py
      execution_mesh.py
      fabric_governance.py
      fabric_snapshot.py
      federation_resources.py
      node_allocator.py
      resource_fabric.py
      resource_models.py
      runtime_sharding.py
      storage_replication.py
      workload_router.py
    federation/
      __init__.py
      collaboration_engine.py
      convergence_analyzer.py
      ecosystem_bridge.py
      ecosystem_identity.py
      ecosystem_policy.py
      ecosystem_registry.py
      federation_engine.py
      federation_governance.py
      federation_memory.py
      federation_models.py
      federation_routing.py
      federation_scheduler.py
      federation_security.py
      federation_snapshot.py
      node_identity.py
      node_registry.py
      shared_knowledge.py
      trust_engine.py
    governance/
      deadlock_detector.py
      degradation_controller.py
      event_governor.py
      execution_governor.py
      execution_throttler.py
      governance_engine.py
      governance_models.py
      loop_detector.py
      memory_controller.py
      provider_rate_control.py
      queue_balancer.py
      recursion_guard.py
      resource_governor.py
      resource_monitor.py
      runtime_limits.py
      self_modification_guard.py
      storm_protection.py
      workload_scheduler.py
    import_fabric/
      __init__.py
      adapter_generator.py
      dependency_mapper.py
      duplication_engine.py
      external_registry.py
      import_orchestrator.py
      merge_analyzer.py
      repo_classifier.py
      repo_cloner.py
      repo_health.py
      repo_indexer.py
      skill_generator.py
      upstream_tracker.py
    kernel/
      adaptive_scheduler.py
      cognition_pipeline.py
      cognition_router.py
      cognitive_kernel.py
      context_engine.py
      execution_context.py
      kernel_governance.py
      kernel_memory.py
      kernel_models.py
      kernel_orchestrator.py
      kernel_snapshot.py
      kernel_state_manager.py
      live_kernel.py
      orchestration_context.py
      runtime_awareness.py
      semantic_executor.py
    knowledge/
      concept_extractor.py
      context_linker.py
      knowledge_engine.py
      knowledge_models.py
      knowledge_query.py
      memory_indexer.py
      operational_context.py
      relationship_inference.py
      semantic_graph.py
      semantic_memory.py
      semantic_search.py
      temporal_memory.py
    knowledge_graph/
      __init__.py
      graph_store.py
      memory_consolidator.py
      semantic_linker.py
    labs/
      __init__.py
      architecture_analyzer.py
      lab_memory.py
      lab_scanner.py
      orchestration_detector.py
      pattern_extractor.py
    learning/
      __init__.py
      adaptive_routing.py
      capability_evolution.py
      execution_learning.py
      failure_learning.py
      learning_engine.py
      learning_models.py
      learning_snapshot.py
      orchestration_learning.py
      pattern_memory.py
      prompt_learning.py
      provider_learning.py
      specialization_engine.py
    lifecycle/
      bootstrap.py
    local_runtime/
      __init__.py
      local_agent_runtime.py
      local_executor.py
      local_task_queue.py
      process_supervisor.py
      runtime_persistence.py
      runtime_watchdog.py
      sandbox_runner.py
      terminal_bridge.py
    memory/
      __init__.py
      code_evolution_memory.py
      consolidation_engine.py
      context_snapshot.py
      memory_engine.py
      memory_manager.py
      memory_store.py
      models.py
      project_families.py
      relationship_engine.py
      repo_similarity.py
    migration/
      __init__.py
      dependency_scanner.py
      import_rewriter.py
      migration_engine.py
      migration_manifest.py
      module_classifier.py
      module_exporter.py
    model_router/
      fallback_router.py
      inference_dispatcher.py
      local_provider_adapter.py
      model_health.py
      model_registry.py
      routing_engine.py
    node_runtime/
      capability_advertiser.py
      node_health.py
      node_identity.py
      node_registry.py
      remote_task_schema.py
    observability/
      event_stream.py
      execution_journal.py
      logger.py
      runtime_metrics.py
    operator/
      __init__.py
      attachment_router.py
      autonomous_operator.py
      autonomous_scheduler.py
      background_runtime.py
      capability_extractor.py
      conversation_indexer.py
      env_manager.py
      execution_supervisor.py
      project_classifier.py
      provider_sync.py
      repo_consolidator.py
      self_improvement_loop.py
      task_daemon.py
      workspace_mapper.py
    overseer/
      overseer.py
    planning/
      capability_gap_detector.py
      dependency_planner.py
      milestone_tracker.py
      roadmap_engine.py
      strategic_memory.py
    providers/
      conversation_classifier.py
      conversation_memory.py
      knowledge_normalizer.py
      model_router.py
      provider_registry.py
      provider_runtime.py
      base/
        provider_base.py
      browser/
        browser_manager.py
        recovery_connectors.py
      chatgpt/
        chatgpt_provider.py
      claude/
        __init__.py
        claude_provider.py
      conversation_sync/
        __init__.py
        ingestion_engine.py
      custom/
        __init__.py
        custom_provider.py
      deepseek/
        __init__.py
        deepseek_provider.py
      gemini/
        __init__.py
        gemini_provider.py
      grok/
        __init__.py
        grok_provider.py
      local_ai_fabric/
        __init__.py
        ollama_adapter.py
        open_webui_adapter.py
        provider_factory.py
      models/
        __init__.py
        conversation.py
      ollama/
        __init__.py
        ollama_provider.py
      openai/
        __init__.py
        openai_provider.py
      openrouter/
        __init__.py
        openrouter_provider.py
      openwebui/
        openwebui_provider.py
      performance/
        __init__.py
        health_monitor.py
        provider_affinity_engine.py
        provider_benchmark.py
        provider_capability_matrix.py
        provider_cost_optimizer.py
        provider_memory_profiles.py
        provider_routing_engine.py
        provider_scoring.py
      poisongpt/
        __init__.py
        poisongpt_provider.py
      proxima/
        proxima_bridge.py
      qwen/
        __init__.py
        qwen_provider.py
      session/
        session_manager.py
      z/
        __init__.py
        z_provider.py
    provider_memory/
      __init__.py
      models.py
      project_manager.py
      relationship_manager.py
    provider_mesh/
      capability_router.py
      consensus_engine.py
      disagreement_detector.py
      latency_router.py
      provider_orchestrator.py
      provider_ranker.py
      synthesis_engine.py
    provider_sync/
      __init__.py
      conversation_indexer.py
      provider_health.py
      provider_memory_sync.py
      provider_registry.py
      sync_engine.py
    realtime/
      realtime_broadcast.py
      websocket_manager.py
    recovery/
      crash_classifier.py
      degradation_manager.py
      health_monitor.py
      isolation_engine.py
      memory_recovery.py
      node_recovery.py
      orchestration_recovery.py
      provider_recovery.py
      recovery_engine.py
      recovery_memory.py
      recovery_models.py
      recovery_snapshot.py
      repair_chain.py
      rollback_recovery.py
      runtime_recovery.py
      service_restarter.py
      state_rebuilder.py
    repository_cognition/
      __init__.py
      architecture_mapper.py
      repo_scanner.py
      repository_civilizer.py
    repository_intelligence/
      __init__.py
      duplicate_detector.py
      external_repos.py
      github_client.py
      intelligence_engine.py
      models.py
      operational_feed.py
      repo_classifier.py
      repo_federation.py
      repo_graph.py
      repo_importer.py
      repo_watchers.py
      scanner.py
      tech_detector.py
      tree_generator.py
    research/
      architecture_lab.py
      benchmark_models.py
      comparative_analysis.py
      experiment_memory.py
      experiment_scheduler.py
      experiment_snapshot.py
      experimentation_engine.py
      isolation_controller.py
      prototype_engine.py
      provider_benchmarking.py
      research_context.py
      research_engine.py
      research_models.py
      sandbox_runtime.py
      technology_evaluator.py
    runtime/
      __init__.py
      health_score.py
      reality_diff.py
      reality_snapshot.py
      runtime.py
      runtime_path_validator.py
      runtime_profile.py
      runtime_state_broadcast.py
      runtime_state_store.py
      safe_action_queue.py
    runtime_daemon/
      __init__.py
      daemon.py
      heartbeat.py
      process_registry.py
      supervisor.py
      watchdog.py
    runtime_state/
      runtime_state.py
    sandbox/
      execution_journal.py
      execution_limits.py
      isolated_runtime.py
      rollback_runtime.py
      runtime_replay.py
      snapshot_manager.py
    search/
      internal_search_engine.py
    security/
      __init__.py
      vault.py
    self_evolution/
      architecture_optimizer.py
      autonomous_refactorer.py
      benchmark_engine.py
      capability_expander.py
      evolution_engine.py
      evolution_guardrails.py
      evolution_memory.py
      patch_candidate_generator.py
      patch_generator.py
      promotion_engine.py
      regression_guard.py
      rollback_manager.py
      safety_validator.py
      sandbox_runner.py
      self_analysis_engine.py
    self_healing/
      __init__.py
      degraded_mode_router.py
      runtime_recovery.py
    storage/
      database.py
      event_store.py
      init_db.py
      models.py
      storage_manager.py
    strategy/
      architecture_forecaster.py
      convergence_planning.py
      debt_predictor.py
      ecosystem_planner.py
      execution_strategy.py
      goal_engine.py
      milestone_engine.py
      objective_tracker.py
      planning_context.py
      priority_engine.py
      roadmap_engine.py
      roadmap_models.py
      strategic_memory.py
      strategic_simulation.py
      strategy_engine.py
      strategy_snapshot.py
      sustainability_engine.py
    telemetry/
      anomaly_metrics.py
      execution_analytics.py
      metrics_collector.py
      resource_monitor.py
      runtime_profiler.py
    update/
      artifact_downloader.py
      release_checker.py
      rollback_manager.py
      safe_updater.py
      update_engine.py
      version_registry.py
    validation/
      event_validator.py
    workspace/
      __init__.py
      attachment_classifier.py
      cognitive_filesystem.py
      conversation_linker.py
      duplicate_projects.py
      file_lineage.py
      project_families.py
      project_health.py
      project_identity.py
      repository_relationships.py
      semantic_project_mapper.py
      workspace_context.py
      workspace_engine.py
      workspace_graph.py
      workspace_manager.py
  DGM-MAT-Agents/
    .gitignore
    README.md
    architecture.md
    ecosystem.json
    health.json
  DGM-MAT-Assets/
    .gitignore
    README.md
    architecture.md
    ecosystem.json
    health.json
  DGM-MAT-Cluster/
    .gitignore
    README.md
    architecture.md
    ecosystem.json
    health.json
  DGM-MAT-Connectors/
    .gitignore
    README.md
    architecture.md
    ecosystem.json
    health.json
  DGM-MAT-Deploy/
    .gitignore
    README.md
    architecture.md
    ecosystem.json
    health.json
  DGM-MAT-Labs/
    .gitignore
    README.md
    architecture.md
    ecosystem.json
    health.json
  DGM-MAT-Marketplace/
    .gitignore
    README.md
    architecture.md
    ecosystem.json
    health.json
  DGM-MAT-Media/
    .gitignore
    README.md
    architecture.md
    ecosystem.json
    health.json
  DGM-MAT-Memory/
    .gitignore
    README.md
    architecture.md
    ecosystem.json
    health.json
  DGM-MAT-Mobile/
    .gitignore
    README.md
    architecture.md
    ecosystem.json
    health.json
  DGM-MAT-Orchestrator/
    .gitignore
    README.md
    architecture.md
    ecosystem.json
    health.json
  DGM-MAT-Plugins/
    .gitignore
    README.md
    architecture.md
    ecosystem.json
    health.json
  DGM-MAT-Providers/
    .gitignore
    README.md
    architecture.md
    ecosystem.json
    health.json
  DGM-MAT-Runtime/
    .gitignore
    README.md
    architecture.md
    ecosystem.json
    health.json
  DGM-MAT-Studio/
    .gitignore
    README.md
    architecture.md
    ecosystem.json
    health.json
  docs/
    ARCHITECTURE_GUARDRAILS.md
    AUTONOMOUS_RUNTIME.md
    BUILD_EXE_RECOVERY_PLAN.md
    COCKPIT_CONVERGENCE_PLAN.md
    COGNITIVE_RUNTIME.md
    DEPENDENCY_CONVERGENCE_REPORT.md
    OPERATIONAL_CONVERGENCE_ROADMAP.md
    OPERATIONAL_RUNTIME.md
    PHASE_HISTORY.md
    SYSTEM_STATUS_REPORT.md
    architecture/
      core.md
    ecosystem/
      agents.md
      events.md
      protocol.md
      topology.md
    ecosystems/
      model.md
    governance/
      evolution.md
      overseer.md
      rules.md
    memory/
      model.md
  legacy/
    architecture.md
    contracts/
      README.md
      agent_contract.json
    core/
      __init__.py
      agents/
        __init__.py
        base.py
        memory_sync_agent.py
        overseer_agent.py
        prompt_intelligence_agent.py
        provider_connector_agent.py
        repo_intelligence_agent.py
        validation_agent.py
      cockpit/
        interface.py
      deployment/
        manager.py
      ecosystem_state/
        __init__.py
        manager.py
      event_bus/
        __init__.py
        bus.py
      gap_detection/
        __init__.py
        detector.py
      git_engine/
        git_manager.py
      health/
        calculator.py
      knowledge_integration/
        __init__.py
        processor.py
      memory/
        __init__.py
        engine.py
        sync.py
      meta_reasoning/
        __init__.py
        orchestrator.py
      observability/
        __init__.py
        logger.py
        metrics.py
      overseer/
        __init__.py
        overseer.py
      prompt_intelligence/
        __init__.py
        generator.py
      prompt_library/
        __init__.py
        genome.py
      providers/
        __init__.py
        isolated_session.py
      repository_intelligence/
        __init__.py
        analyzer.py
        auto_repair.py
      self_healing/
        engine.py
      validation/
        __init__.py
        drift.py
        engine.py
    schemas/
      event.schema.json
    tests/
      test_drift.py
      test_phase6.py
      test_phase7.py
      test_system.py
  memory_sync/
    phase41_lite_learnings.json
  Persist-Node/
    ecosystem.json
    health.json
  requirements/
    base.txt
    build.txt
    cockpit.txt
    dev.txt
    research.txt
    runtime.txt
  scripts/
    autonomous_dry_run.py
    executable_runtime_test.py
    extract_repo.py
    fase_43_6_force_cognition.py
    fase_43_6_force_cognition_real.py
    fase_43_6_observations.json
    fase_43_6_observations_real.json
    fase_43_6_report.json
    fase_43_6_report_real.json
    generate_validation_reports.py
    phase35_imports.py
    phase_finalizer.py
    repo_bootstrap_interactive.py
    runtime_smoke_test.py
    stress_test_memory.py
    stress_test_providers.py
    validate_dependencies.py
    validate_executable.py
    validate_storage.py
    verify_cockpit_persistence.py
    verify_mission_recovery.py
    autostart/
      __init__.py
      autonomous_loop.py
      boot_runtime.py
      recovery_monitor.py
      restore_runtime.py
      restore_sessions.py
      start_cockpit.py
      start_daemon.py
      start_dgm_mat.py
      start_runtime.py
      worker_cluster.py
    bootstrap_tests/
      test_bootstrap_logic.py
  shared/
    config/
      settings.py
    enums/
      event_priority.py
    models/
      __init__.py
      event.py
  tests/
    __init__.py
    test_phase35_autonomy.py
    test_phase35_cognition.py
    test_phase35_governance.py
    autonomous_dev/
      test_repository_extractor.py
    autonomy/
      test_analysis.py
      test_continuous_runtime.py
      test_degraded_mode.py
      test_engines.py
      test_loop.py
      test_mission_system.py
      test_phase37_logic.py
      test_scheduler.py
    bootstrap/
      __init__.py
      test_bootstrap_logic.py
    cockpit/
      test_cockpit_boot.py
      test_cockpit_sync.py
      test_realtime_integration.py
    daemon/
      test_daemon_persistence.py
    ecosystem/
      test_protection_rules.py
      test_reality_sync.py
    execution_fabric/
      __init__.py
      test_execution_fabric.py
      test_execution_logic.py
    import_fabric/
      __init__.py
      test_import_intelligence_v7.py
      test_phase15_16_17_import.py
      test_repo_import_validation.py
      test_repo_importer.py
    integration/
      __init__.py
      test_api_endpoints.py
      test_ecosystem.py
      test_ecosystem_materializer.py
      test_federation_layer.py
      test_governance_sim.py
      test_knowledge_fabric.py
      test_provider_sync.py
      test_repository_intelligence.py
      test_research_layer.py
      test_runtime_truth.py
      test_storage_architecture.py
      test_strategic_orchestration.py
    knowledge_graph/
      test_consolidation.py
    migration/
      test_engine.py
      test_rewriter.py
      test_scanner.py
    operational/
      test_cockpit_mission_trace.py
      test_master_runtime.py
      test_phase37_operational.py
      test_recovery.py
      test_work_queue.py
    platform/
      test_cognition_survival.py
      test_runtime_restoration.py
    provider_mesh/
      test_mesh_orchestration.py
    provider_sync/
      test_sync.py
    repository_cognition/
      test_civilization.py
      test_indexing.py
    runtime/
      test_health_breakdown.py
      test_health_score.py
      test_reality_diff.py
      test_reality_snapshot.py
      test_safe_action_queue.py
      test_smoke.py
    runtime_daemon/
      test_daemon.py
      test_recovery.py
    sandbox/
      test_sandbox_security.py
    security/
      __init__.py
    self_evolution/
      test_self_analysis.py
    system/
      test_repo_scanning.py
      test_worktree_execution.py
    unit/
      __init__.py
      test_dependency_integrity.py
      test_operational_stability.py
      test_persistent_paths.py
      test_provider_orchestration_new.py
      test_provider_registry.py
      test_runtime.py
      test_vault_security.py
  tools/
    controlled_import.py
    import_engine.py
    repo_control_panel/
      app.py
      github_client.py
      repo_manager.py
```

## Python packages

### `__root__`
- fix_verify
- force_approve
- gm
- inspect_db
- main
- observe
- pm
- scan
- test_pyside6
- verify_all_phase37_38
- verify_architecture
- verify_cockpit
- verify_cockpit_phase38
- verify_widgets

### `cockpit`
- __init__
- main_window
- realtime_client

### `cockpit.app`
- __init__
- app_foundation
- main
- websocket_client

### `cockpit.approvals`
- patch_review
- patch_review_ui
- queue_widget

### `cockpit.autonomy`
- monitor_widget

### `cockpit.memory`
- inspector_widget

### `cockpit.providers`
- login_form
- management_widget

### `cockpit.streaming`
- realtime_client

### `cockpit.widgets`
- activity_stream_widget
- agent_widget
- architecture_graph_view
- autonomous_tasks_widget
- autonomy_dashboard
- cognitive_dashboard
- command_console
- dashboard_widget
- duplicate_detection_widget
- ecosystem_graph_widget
- event_stream_widget
- execution_feed
- execution_queue_widget
- federation_widget
- governance_widget
- health_graph
- imported_repos_widget
- knowledge_feed_widget
- knowledge_graph_widget
- learning_dashboard_widget
- local_execution_widget
- logs_widget
- mesh_monitor_widget
- mission_widget
- operational_dashboard
- operational_search_widget
- project_families_widget
- provider_conversations_widget
- research_widget
- runtime_health_widget
- self_improvement_widget
- strategy_widget
- tech_debt_dashboard
- technical_debt_widget
- workspace_graph_widget

### `cockpit.workspace`
- chat_widget
- cognition_graph
- execution_timeline_widget
- memory_graph
- task_feed_widget

### `core.agents`
- architect_agent
- autonomy_agent
- base_agent
- debug_agent
- devops_agent
- isolated_runtime
- memory_agent
- provider_agent
- refactor_agent
- repo_agent
- research_agent
- runtime_agent
- security_agent
- self_improvement_agent
- ui_agent
- watchdog

### `core.agents.specialization`
- __init__
- adaptive_specialization
- agent_profiler
- capability_allocator
- execution_roles
- provider_affinity
- runtime_affinity
- skill_distribution
- specialization_registry
- workload_optimizer

### `core.api`
- api_server
- mobile_bridge
- runtime_api

### `core.autonomous_dev`
- __init__
- architecture_optimizer
- autonomous_dev_engine
- cleanup_engine
- dead_code_detector
- dependency_fixer
- issue_detector
- merge_planner
- repo_refactor_loop
- repository_extractor
- roadmap_executor
- self_patch_engine
- task_generator
- technical_debt_engine

### `core.autonomy`
- autonomous_loop
- mission_engine
- mission_models
- models
- priority_engine
- repair_suggester
- repo_analysis_pipeline
- safe_autonomous_executor
- self_improvement_planner
- task_engine
- task_generator
- task_planner
- task_queue
- work_queue
- worker_allocator

### `core.autonomy.active_runtime`
- autonomy_cycle
- cognition_loop
- execution_director
- learning_loop
- objective_engine
- strategic_planner

### `core.autonomy.continuous_runtime`
- adaptive_router
- autonomous_director
- cognition_scheduler
- evolution_engine
- execution_coordinator
- lifecycle_manager
- observation_engine
- planning_engine
- reflection_engine
- runtime_core

### `core.autonomy.scheduler`
- __init__
- execution_loop
- priority_router
- retry_manager
- scheduler_engine
- task_queue

### `core.bootstrap`
- __init__

### `core.bootstrap.core`
- __init__
- bootstrap_context
- bootstrap_storage
- dependency_loader
- environment_detector

### `core.bootstrap.federation`
- __init__

### `core.bootstrap.providers`
- __init__

### `core.bootstrap.runtime`
- __init__
- bootstrap_engine
- bootstrap_sequence

### `core.bootstrap.ui`
- __init__

### `core.cockpit_runtime`
- __init__
- autonomy_status_api
- cognition_visualizer
- execution_dashboard
- live_task_feed
- realtime_runtime_api
- runtime_metrics
- telemetry_stream
- websocket_runtime

### `core.cognition`
- architecture_graph
- architecture_memory
- cognition_graph
- cognition_models
- cognition_snapshot
- cognitive_analysis_engine
- convergence_engine
- dependency_mapper
- ecosystem_engine
- ecosystem_health
- fragmentation_detector
- impact_analyzer
- pattern_extractor
- risk_predictor
- topology_engine

### `core.connectors`
- obsidian_connector

### `core.connectors.adapters`
- AIClient2API_adapter
- gpt4free_adapter

### `core.development`
- architecture_validator
- branch_execution
- code_generation
- development_engine
- development_memory
- development_models
- development_snapshot
- execution_fabric
- feature_planner
- implementation_engine
- integration_engine
- merge_preparation
- refactor_engine
- repair_execution
- test_orchestrator
- validation_engine

### `core.distributed`
- __init__
- distributed_memory
- mesh_models
- node_capabilities
- node_failover
- node_heartbeat
- node_identity
- node_manager
- node_registry
- node_state
- node_sync

### `core.ecosystem`
- ecosystem_lifecycle
- ecosystem_materializer
- ecosystem_models
- ecosystem_registry
- ecosystem_validator
- reality_sync_engine
- safe_import_system

### `core.event_bus`
- event_bus

### `core.evolution`
- abstraction_optimizer
- adaptive_patterns
- architecture_mutation
- convergence_optimizer
- degradation_analyzer
- evolution_engine
- evolution_memory
- evolution_snapshot
- mutation_simulator
- orchestration_optimizer
- regeneration_engine
- regeneration_models
- runtime_regenerator
- semantic_refactor
- structural_forecaster

### `core.execution`
- __init__
- approval_manager
- branch_manager
- execution_context
- execution_engine
- execution_models
- git_utils
- merge_guard
- repair_loop
- rollback_engine
- worktree_manager

### `core.execution_fabric`
- __init__
- autonomous_executor
- branch_orchestrator
- execution_cycles
- execution_fabric
- execution_memory
- execution_recovery
- execution_state_machine
- execution_supervisor
- safe_patch_engine
- task_dispatcher
- validation_pipeline
- worktree_runtime

### `core.fabric`
- cluster_scheduler
- cognition_cluster
- distributed_storage
- execution_mesh
- fabric_governance
- fabric_snapshot
- federation_resources
- node_allocator
- resource_fabric
- resource_models
- runtime_sharding
- storage_replication
- workload_router

### `core.federation`
- __init__
- collaboration_engine
- convergence_analyzer
- ecosystem_bridge
- ecosystem_identity
- ecosystem_policy
- ecosystem_registry
- federation_engine
- federation_governance
- federation_memory
- federation_models
- federation_routing
- federation_scheduler
- federation_security
- federation_snapshot
- node_identity
- node_registry
- shared_knowledge
- trust_engine

### `core.governance`
- deadlock_detector
- degradation_controller
- event_governor
- execution_governor
- execution_throttler
- governance_engine
- governance_models
- loop_detector
- memory_controller
- provider_rate_control
- queue_balancer
- recursion_guard
- resource_governor
- resource_monitor
- runtime_limits
- self_modification_guard
- storm_protection
- workload_scheduler

### `core.import_fabric`
- __init__
- adapter_generator
- dependency_mapper
- duplication_engine
- external_registry
- import_orchestrator
- merge_analyzer
- repo_classifier
- repo_cloner
- repo_health
- repo_indexer
- skill_generator
- upstream_tracker

### `core.kernel`
- adaptive_scheduler
- cognition_pipeline
- cognition_router
- cognitive_kernel
- context_engine
- execution_context
- kernel_governance
- kernel_memory
- kernel_models
- kernel_orchestrator
- kernel_snapshot
- kernel_state_manager
- live_kernel
- orchestration_context
- runtime_awareness
- semantic_executor

### `core.knowledge`
- concept_extractor
- context_linker
- knowledge_engine
- knowledge_models
- knowledge_query
- memory_indexer
- operational_context
- relationship_inference
- semantic_graph
- semantic_memory
- semantic_search
- temporal_memory

### `core.knowledge_graph`
- __init__
- graph_store
- memory_consolidator
- semantic_linker

### `core.labs`
- __init__
- architecture_analyzer
- lab_memory
- lab_scanner
- orchestration_detector
- pattern_extractor

### `core.learning`
- __init__
- adaptive_routing
- capability_evolution
- execution_learning
- failure_learning
- learning_engine
- learning_models
- learning_snapshot
- orchestration_learning
- pattern_memory
- prompt_learning
- provider_learning
- specialization_engine

### `core.lifecycle`
- bootstrap

### `core.local_runtime`
- __init__
- local_agent_runtime
- local_executor
- local_task_queue
- process_supervisor
- runtime_persistence
- runtime_watchdog
- sandbox_runner
- terminal_bridge

### `core.memory`
- __init__
- code_evolution_memory
- consolidation_engine
- context_snapshot
- memory_engine
- memory_manager
- memory_store
- models
- project_families
- relationship_engine
- repo_similarity

### `core.migration`
- __init__
- dependency_scanner
- import_rewriter
- migration_engine
- migration_manifest
- module_classifier
- module_exporter

### `core.model_router`
- fallback_router
- inference_dispatcher
- local_provider_adapter
- model_health
- model_registry
- routing_engine

### `core.node_runtime`
- capability_advertiser
- node_health
- node_identity
- node_registry
- remote_task_schema

### `core.observability`
- event_stream
- execution_journal
- logger
- runtime_metrics

### `core.operator`
- __init__
- attachment_router
- autonomous_operator
- autonomous_scheduler
- background_runtime
- capability_extractor
- conversation_indexer
- env_manager
- execution_supervisor
- project_classifier
- provider_sync
- repo_consolidator
- self_improvement_loop
- task_daemon
- workspace_mapper

### `core.overseer`
- overseer

### `core.planning`
- capability_gap_detector
- dependency_planner
- milestone_tracker
- roadmap_engine
- strategic_memory

### `core.provider_memory`
- __init__
- models
- project_manager
- relationship_manager

### `core.provider_mesh`
- capability_router
- consensus_engine
- disagreement_detector
- latency_router
- provider_orchestrator
- provider_ranker
- synthesis_engine

### `core.provider_sync`
- __init__
- conversation_indexer
- provider_health
- provider_memory_sync
- provider_registry
- sync_engine

### `core.providers`
- conversation_classifier
- conversation_memory
- knowledge_normalizer
- model_router
- provider_registry
- provider_runtime

### `core.providers.base`
- provider_base

### `core.providers.browser`
- browser_manager
- recovery_connectors

### `core.providers.chatgpt`
- chatgpt_provider

### `core.providers.claude`
- __init__
- claude_provider

### `core.providers.conversation_sync`
- __init__
- ingestion_engine

### `core.providers.custom`
- __init__
- custom_provider

### `core.providers.deepseek`
- __init__
- deepseek_provider

### `core.providers.gemini`
- __init__
- gemini_provider

### `core.providers.grok`
- __init__
- grok_provider

### `core.providers.local_ai_fabric`
- __init__
- ollama_adapter
- open_webui_adapter
- provider_factory

### `core.providers.models`
- __init__
- conversation

### `core.providers.ollama`
- __init__
- ollama_provider

### `core.providers.openai`
- __init__
- openai_provider

### `core.providers.openrouter`
- __init__
- openrouter_provider

### `core.providers.openwebui`
- openwebui_provider

### `core.providers.performance`
- __init__
- health_monitor
- provider_affinity_engine
- provider_benchmark
- provider_capability_matrix
- provider_cost_optimizer
- provider_memory_profiles
- provider_routing_engine
- provider_scoring

### `core.providers.poisongpt`
- __init__
- poisongpt_provider

### `core.providers.proxima`
- proxima_bridge

### `core.providers.qwen`
- __init__
- qwen_provider

### `core.providers.session`
- session_manager

### `core.providers.z`
- __init__
- z_provider

### `core.realtime`
- realtime_broadcast
- websocket_manager

### `core.recovery`
- crash_classifier
- degradation_manager
- health_monitor
- isolation_engine
- memory_recovery
- node_recovery
- orchestration_recovery
- provider_recovery
- recovery_engine
- recovery_memory
- recovery_models
- recovery_snapshot
- repair_chain
- rollback_recovery
- runtime_recovery
- service_restarter
- state_rebuilder

### `core.repository_cognition`
- __init__
- architecture_mapper
- repo_scanner
- repository_civilizer

### `core.repository_intelligence`
- __init__
- duplicate_detector
- external_repos
- github_client
- intelligence_engine
- models
- operational_feed
- repo_classifier
- repo_federation
- repo_graph
- repo_importer
- repo_watchers
- scanner
- tech_detector
- tree_generator

### `core.research`
- architecture_lab
- benchmark_models
- comparative_analysis
- experiment_memory
- experiment_scheduler
- experiment_snapshot
- experimentation_engine
- isolation_controller
- prototype_engine
- provider_benchmarking
- research_context
- research_engine
- research_models
- sandbox_runtime
- technology_evaluator

### `core.runtime`
- __init__
- health_score
- reality_diff
- reality_snapshot
- runtime
- runtime_path_validator
- runtime_profile
- runtime_state_broadcast
- runtime_state_store
- safe_action_queue

### `core.runtime_daemon`
- __init__
- daemon
- heartbeat
- process_registry
- supervisor
- watchdog

### `core.runtime_state`
- runtime_state

### `core.sandbox`
- execution_journal
- execution_limits
- isolated_runtime
- rollback_runtime
- runtime_replay
- snapshot_manager

### `core.search`
- internal_search_engine

### `core.security`
- __init__
- vault

### `core.self_evolution`
- architecture_optimizer
- autonomous_refactorer
- benchmark_engine
- capability_expander
- evolution_engine
- evolution_guardrails
- evolution_memory
- patch_candidate_generator
- patch_generator
- promotion_engine
- regression_guard
- rollback_manager
- safety_validator
- sandbox_runner
- self_analysis_engine

### `core.self_healing`
- __init__
- degraded_mode_router
- runtime_recovery

### `core.storage`
- database
- event_store
- init_db
- models
- storage_manager

### `core.strategy`
- architecture_forecaster
- convergence_planning
- debt_predictor
- ecosystem_planner
- execution_strategy
- goal_engine
- milestone_engine
- objective_tracker
- planning_context
- priority_engine
- roadmap_engine
- roadmap_models
- strategic_memory
- strategic_simulation
- strategy_engine
- strategy_snapshot
- sustainability_engine

### `core.telemetry`
- anomaly_metrics
- execution_analytics
- metrics_collector
- resource_monitor
- runtime_profiler

### `core.update`
- artifact_downloader
- release_checker
- rollback_manager
- safe_updater
- update_engine
- version_registry

### `core.validation`
- event_validator

### `core.workspace`
- __init__
- attachment_classifier
- cognitive_filesystem
- conversation_linker
- duplicate_projects
- file_lineage
- project_families
- project_health
- project_identity
- repository_relationships
- semantic_project_mapper
- workspace_context
- workspace_engine
- workspace_graph
- workspace_manager

### `legacy.core`
- __init__

### `legacy.core.agents`
- __init__
- base
- memory_sync_agent
- overseer_agent
- prompt_intelligence_agent
- provider_connector_agent
- repo_intelligence_agent
- validation_agent

### `legacy.core.cockpit`
- interface

### `legacy.core.deployment`
- manager

### `legacy.core.ecosystem_state`
- __init__
- manager

### `legacy.core.event_bus`
- __init__
- bus

### `legacy.core.gap_detection`
- __init__
- detector

### `legacy.core.git_engine`
- git_manager

### `legacy.core.health`
- calculator

### `legacy.core.knowledge_integration`
- __init__
- processor

### `legacy.core.memory`
- __init__
- engine
- sync

### `legacy.core.meta_reasoning`
- __init__
- orchestrator

### `legacy.core.observability`
- __init__
- logger
- metrics

### `legacy.core.overseer`
- __init__
- overseer

### `legacy.core.prompt_intelligence`
- __init__
- generator

### `legacy.core.prompt_library`
- __init__
- genome

### `legacy.core.providers`
- __init__
- isolated_session

### `legacy.core.repository_intelligence`
- __init__
- analyzer
- auto_repair

### `legacy.core.self_healing`
- engine

### `legacy.core.validation`
- __init__
- drift
- engine

### `legacy.tests`
- test_drift
- test_phase6
- test_phase7
- test_system

### `scripts`
- autonomous_dry_run
- executable_runtime_test
- extract_repo
- fase_43_6_force_cognition
- fase_43_6_force_cognition_real
- generate_validation_reports
- phase35_imports
- phase_finalizer
- repo_bootstrap_interactive
- runtime_smoke_test
- stress_test_memory
- stress_test_providers
- validate_dependencies
- validate_executable
- validate_storage
- verify_cockpit_persistence
- verify_mission_recovery

### `scripts.autostart`
- __init__
- autonomous_loop
- boot_runtime
- recovery_monitor
- restore_runtime
- restore_sessions
- start_cockpit
- start_daemon
- start_dgm_mat
- start_runtime
- worker_cluster

### `scripts.bootstrap_tests`
- test_bootstrap_logic

### `shared.config`
- settings

### `shared.enums`
- event_priority

### `shared.models`
- __init__
- event

### `tests`
- __init__
- test_phase35_autonomy
- test_phase35_cognition
- test_phase35_governance

### `tests.autonomous_dev`
- test_repository_extractor

### `tests.autonomy`
- test_analysis
- test_continuous_runtime
- test_degraded_mode
- test_engines
- test_loop
- test_mission_system
- test_phase37_logic
- test_scheduler

### `tests.bootstrap`
- __init__
- test_bootstrap_logic

### `tests.cockpit`
- test_cockpit_boot
- test_cockpit_sync
- test_realtime_integration

### `tests.daemon`
- test_daemon_persistence

### `tests.ecosystem`
- test_protection_rules
- test_reality_sync

### `tests.execution_fabric`
- __init__
- test_execution_fabric
- test_execution_logic

### `tests.import_fabric`
- __init__
- test_import_intelligence_v7
- test_phase15_16_17_import
- test_repo_import_validation
- test_repo_importer

### `tests.integration`
- __init__
- test_api_endpoints
- test_ecosystem
- test_ecosystem_materializer
- test_federation_layer
- test_governance_sim
- test_knowledge_fabric
- test_provider_sync
- test_repository_intelligence
- test_research_layer
- test_runtime_truth
- test_storage_architecture
- test_strategic_orchestration

### `tests.knowledge_graph`
- test_consolidation

### `tests.migration`
- test_engine
- test_rewriter
- test_scanner

### `tests.operational`
- test_cockpit_mission_trace
- test_master_runtime
- test_phase37_operational
- test_recovery
- test_work_queue

### `tests.platform`
- test_cognition_survival
- test_runtime_restoration

### `tests.provider_mesh`
- test_mesh_orchestration

### `tests.provider_sync`
- test_sync

### `tests.repository_cognition`
- test_civilization
- test_indexing

### `tests.runtime`
- test_health_breakdown
- test_health_score
- test_reality_diff
- test_reality_snapshot
- test_safe_action_queue
- test_smoke

### `tests.runtime_daemon`
- test_daemon
- test_recovery

### `tests.sandbox`
- test_sandbox_security

### `tests.security`
- __init__

### `tests.self_evolution`
- test_self_analysis

### `tests.system`
- test_repo_scanning
- test_worktree_execution

### `tests.unit`
- __init__
- test_dependency_integrity
- test_operational_stability
- test_persistent_paths
- test_provider_orchestration_new
- test_provider_registry
- test_runtime
- test_vault_security

### `tools`
- controlled_import
- import_engine

### `tools.repo_control_panel`
- app
- github_client
- repo_manager
