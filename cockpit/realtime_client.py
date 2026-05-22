import json
import threading
import websocket

class RealtimeClient:
    def __init__(
        self,
        on_message,
    ):
        self.on_message = on_message
        self.ws = None

    def start(self):
        def run():
            self.ws = websocket.WebSocketApp(
                "ws://127.0.0.1:8181/ws",
                on_message=self._handle,
            )
            self.ws.run_forever()
        thread = threading.Thread(
            target=run,
            daemon=True,
        )
        thread.start()

    def _handle(
        self,
        ws,
        message,
    ):
        try:
            data = json.loads(message)
            self.on_message(data)
        except Exception:
            pass
