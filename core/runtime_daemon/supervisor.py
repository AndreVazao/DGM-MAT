import time
import subprocess
import threading
from core.observability.logger import dgm_logger

class ModuleSupervisor:
    def __init__(self):
        self.procs = {}
        self._running = False
        self._thread = None

    def start_module(self, name: str, cmd: list):
        if name in self.procs: return
        try:
            p = subprocess.Popen(cmd)
            self.procs[name] = {"p": p, "cmd": cmd, "restarts": 0, "last_restart": time.time()}
            dgm_logger.info(f"Supervisor: Started module '{name}'")
        except Exception as e:
            dgm_logger.error(f"Supervisor: Failed to start '{name}': {e}")

    def start_monitoring(self):
        self._running = True
        self._thread = threading.Thread(target=self._monitor, daemon=True)
        self._thread.start()

    def _monitor(self):
        while self._running:
            try:
                for name, data in list(self.procs.items()):
                    if data["p"].poll() is not None:
                        # Throttled restart
                        if data["restarts"] < 10:
                            now = time.time()
                            if now - data["last_restart"] > 10:
                                dgm_logger.warning(f"Supervisor: Restarting '{name}' (Attempt {data['restarts']+1})")
                                data["restarts"] += 1
                                data["last_restart"] = now
                                data["p"] = subprocess.Popen(data["cmd"])
                            else:
                                dgm_logger.debug(f"Supervisor: Throttling restart for '{name}'")
                        else:
                            dgm_logger.error(f"Supervisor: Module '{name}' EXHAUSTED restarts")
            except Exception as e:
                dgm_logger.error(f"Supervisor: Monitor loop error: {e}")
            time.sleep(10)

    def stop(self):
        self._running = False
        for name, data in self.procs.items():
            dgm_logger.info(f"Supervisor: Terminating '{name}'")
            data["p"].terminate()
            try: data["p"].wait(timeout=5)
            except: data["p"].kill()
