import os
import json
import datetime
import hashlib
from typing import Dict, Any, List

class MemoryEngine:
    def __init__(self, memory_path: str = "core/memory/storage"):
        self.memory_path = memory_path
        os.makedirs(self.memory_path, exist_ok=True)
        self.snapshots_path = os.path.join(self.memory_path, "snapshots")
        os.makedirs(self.snapshots_path, exist_ok=True)

    def save_snapshot(self, category: str, data: Dict[str, Any]) -> str:
        """Save an append-only, versioned snapshot of data."""
        timestamp = datetime.datetime.utcnow().isoformat()
        version = self._get_next_version(category)

        payload = {
            "timestamp": timestamp,
            "category": category,
            "data": data,
            "version": version
        }

        content = json.dumps(payload, indent=2)
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        filename = f"{category}_{version}_{content_hash[:8]}.json"
        filepath = os.path.join(self.snapshots_path, filename)

        # Ensure we don't overwrite (append-only principle)
        if os.path.exists(filepath):
             # This should be rare due to versioning and hash, but for safety:
             timestamp_str = datetime.datetime.utcnow().strftime("%Y%m%d%H%M%S")
             filename = f"{category}_{version}_{content_hash[:8]}_{timestamp_str}.json"
             filepath = os.path.join(self.snapshots_path, filename)

        with open(filepath, 'w') as f:
            f.write(content)

        return filepath

    def _get_next_version(self, category: str) -> int:
        if not os.path.exists(self.snapshots_path):
            return 1
        files = [f for f in os.listdir(self.snapshots_path) if f.startswith(f"{category}_")]
        if not files:
            return 1
        versions = []
        for f in files:
            try:
                parts = f.split('_')
                if len(parts) >= 2:
                    versions.append(int(parts[1]))
            except ValueError:
                continue
        return max(versions) + 1 if versions else 1

    def get_latest(self, category: str) -> Dict[str, Any]:
        """Retrieve the most recent snapshot for a category."""
        if not os.path.exists(self.snapshots_path):
            return {}
        files = [f for f in os.listdir(self.snapshots_path) if f.startswith(f"{category}_")]
        if not files:
            return {}

        def get_version(f):
            try:
                return int(f.split('_')[1])
            except:
                return 0

        latest_file = max(files, key=get_version)
        with open(os.path.join(self.snapshots_path, latest_file), 'r') as f:
            return json.load(f)

    def list_history(self, category: str) -> List[str]:
        """List all snapshots for a category, sorted by version."""
        if not os.path.exists(self.snapshots_path):
            return []
        files = [f for f in os.listdir(self.snapshots_path) if f.startswith(f"{category}_")]

        def get_version(f):
            try:
                return int(f.split('_')[1])
            except:
                return 0

        return sorted(files, key=get_version)
