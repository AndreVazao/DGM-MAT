# DGM-MAT Autonomous Runtime

## Overview
DGM-MAT has evolved from a passive framework into a continuously operating autonomous development system. This document describes the architecture, lifecycle, and safety models of the autonomous runtime.

## Architecture
The autonomous system is built on several key engines:
- **Autonomous Loop Engine**: Perpetually executes a 10-phase cycle.
- **Task Generation Engine**: Discovers work from repository analysis, failures, and provider knowledge.
- **Priority Engine**: Dynamically scores tasks based on impact and risk.
- **Safe Autonomous Executor**: Executes tasks in isolated worktrees with mandatory validation.

## Execution Lifecycle
The 10-phase cycle:
1. **scan_state**: Verify current system health.
2. **collect_inputs**: Gather TODOs, failures, and external insights.
3. **analyze**: Run repo analysis for drift and dead code.
4. **prioritize**: Rank tasks by score.
5. **plan**: Allocate workers and schedule tasks.
6. **execute_safe**: Perform work in isolated worktrees.
7. **validate**: Run tests and verify patches.
8. **persist_memory**: Update long-term memory.
9. **update_metrics**: Push updates to Cockpit.
10. **sleep**: Wait for the next interval.

## Safety Model
- **Isolation**: No work is performed on the main branch. Isolated worktrees only.
- **Rollback**: Every execution has a journaling system for automatic rollback on failure.
- **Approvals**: In `SAFE` mode, merging requires manual approval via Cockpit.
- **Persistence**: State is saved to `.runtime/runtime_state.json` to survive reboots.
