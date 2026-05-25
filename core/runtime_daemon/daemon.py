import time
import signal
import sys
import os
from core.observability.logger import dgm_logger
from core.runtime_daemon.heartbeat import HeartbeatManager
from core.runtime_daemon.process_registry import ProcessRegistry
from core.runtime_daemon.watchdog import RuntimeWatchdog
from core.runtime_daemon.supervisor import ModuleSupervisor

class RuntimeDaemon:
    """
    The main persistent entry point for DGM-MAT.
    Hardened for loop safety and graceful shutdown.
    """
    def __init__(self):
        self.heartbeat = HeartbeatManager()
        self.registry = ProcessRegistry()
        self.watchdog = RuntimeWatchdog(self.heartbeat)
        self.supervisor = ModuleSupervisor()
        self._running = False
        self._shutdown_initiated = False

        # Handle signals
        for sig in (signal.SIGINT, signal.SIGTERM):
            signal.signal(sig, self._handle_exit)

    def run(self):
        dgm_logger.info("RuntimeDaemon: Starting DGM-MAT Persistent Daemon...")
        try:
            self.registry.register_self()
            self.watchdog.start()
            self._running = True

            while self._running:
                try:
                    self.heartbeat.pulse(status="running")
                    self.watchdog.pulse_loop("main_daemon")
                except Exception as e:
                    dgm_logger.error(f"RuntimeDaemon: Loop error: {e}")

                # Mandatory sleep to prevent CPU spin
                time.sleep(30)

        except Exception as e:
            dgm_logger.critical(f"RuntimeDaemon: Fatal crash: {e}")
        finally:
            self.shutdown()

    def _handle_exit(self, signum, frame):
        if self._shutdown_initiated: return
        dgm_logger.info(f"RuntimeDaemon: Received signal {signum}. Initiating graceful shutdown...")
        self._running = False
        self._shutdown_initiated = True

    def shutdown(self):
        dgm_logger.info("RuntimeDaemon: Shutting down subsystems...")
        self.watchdog.stop()
        self.supervisor.stop()
        self.registry.unregister()
        dgm_logger.info("RuntimeDaemon: Shutdown complete.")
        # Ensure we exit
        if not any(arg in sys.argv for arg in ['pytest', 'test']):
            os._exit(0)

if __name__ == "__main__":
    RuntimeDaemon().run()
