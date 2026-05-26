import os
from pathlib import Path

def check_path(path):
    exists = os.path.exists(path)
    print(f"{'OK' if exists else 'MISSING'}: {path}")
    return exists

paths = [
    "core/autonomy/active_runtime/cognition_loop.py",
    "core/autonomy/continuous_runtime/runtime_core.py",
    "core/autonomy/continuous_runtime/lifecycle_manager.py",
    "core/self_evolution/evolution_guardrails.py",
    "core/provider_mesh/provider_orchestrator.py",
    "core/sandbox/isolated_runtime.py",
    "core/telemetry/metrics_collector.py",
    "cockpit/workspace/chat_widget.py",
    "cockpit/app/app_foundation.py",
    "scripts/autostart/start_daemon.py",
    "tests/operational/test_recovery.py"
]

all_ok = True
for p in paths:
    if not check_path(p):
        all_ok = False

if all_ok:
    print("\nALL CRITICAL MODULES VERIFIED.")
else:
    print("\nSOME MODULES ARE MISSING.")
