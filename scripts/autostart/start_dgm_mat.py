import subprocess
import sys
import os

def start():
    print("Starting DGM-MAT Ecosystem...")
    # Start Daemon
    subprocess.Popen([sys.executable, "core/runtime_daemon/daemon.py"])
    # Start Cockpit
    subprocess.Popen([sys.executable, "cockpit/app.py"])

if __name__ == "__main__":
    start()
