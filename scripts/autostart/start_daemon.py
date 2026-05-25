import subprocess
import sys

def start():
    print("Starting DGM-MAT Runtime Daemon...")
    subprocess.Popen([sys.executable, "core/runtime_daemon/daemon.py"])

if __name__ == "__main__":
    start()
