import subprocess
import sys

def start():
    print("Starting DGM-MAT Cockpit...")
    subprocess.Popen([sys.executable, "cockpit/app.py"])

if __name__ == "__main__":
    start()
