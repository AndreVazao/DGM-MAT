import subprocess
import sys
import os
from core.observability.trace_utils import trace_runtime_activation

trace_runtime_activation("RUNTIME_ENTRY:scripts/autostart/start_dgm_mat.py")

def start():
    print("Starting DGM-MAT Ecosystem...")
    # Start Daemon
    trace_runtime_activation("TRACE_RUNTIME_ACTIVATE:core.runtime_daemon.daemon")
    subprocess.Popen([sys.executable, "core/runtime_daemon/daemon.py"])
    # Start Cockpit
    trace_runtime_activation("TRACE_RUNTIME_ACTIVATE:cockpit.app")
    subprocess.Popen([sys.executable, "cockpit/app.py"])

if __name__ == "__main__":
    start()
