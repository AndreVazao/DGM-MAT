from __future__ import annotations

import json
import platform
import urllib.request
from pathlib import Path

DEFAULT_URL = "https://dgm-mat-rendezvous.vercel.app/api/rendezvous"
SECRET_FILE = Path("C:/ProgramasGodMode/DGM-MAT/config/rendezvous.secret")

class RendezvousClient:
    def __init__(self, url: str = DEFAULT_URL, secret_file: Path = SECRET_FILE):
        self.url = url
        self.secret_file = secret_file

    def register(self, node_id: str, node_type: str, name: str, endpoint: str | None, capabilities: list[str], version: str | None = None, ttl_seconds: int = 120) -> dict:
        secret = self.secret_file.read_text(encoding="utf-8").strip()
        payload = {"node_id": node_id, "node_type": node_type, "name": name, "endpoint": endpoint, "capabilities": capabilities, "version": version, "platform": platform.platform(), "ttl_seconds": ttl_seconds}
        request = urllib.request.Request(self.url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type":"application/json", "Authorization":f"Bearer {secret}"}, method="POST")
        with urllib.request.urlopen(request, timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))

    def discover(self) -> list[dict]:
        secret = self.secret_file.read_text(encoding="utf-8").strip()
        request = urllib.request.Request(self.url, headers={"Authorization":f"Bearer {secret}"}, method="GET")
        with urllib.request.urlopen(request, timeout=10) as response:
            return json.loads(response.read().decode("utf-8")).get("nodes", [])
