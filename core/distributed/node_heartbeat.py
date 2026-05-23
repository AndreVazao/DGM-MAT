import time
import threading

class NodeHeartbeat:
    def __init__(self, node_id):
        self.node_id = node_id
        self.running = False

    def start(self):
        self.running = True
        threading.Thread(target=self._loop, daemon=True).start()

    def _loop(self):
        while self.running:
            print(f"Heartbeat sent for {self.node_id}")
            time.sleep(5)
