import json
import os
from datetime import datetime

REGISTRY_FILE = "tools/repo_control_panel/registry.json"

class RepoManager:
    def __init__(self):
        self.repos = self.load()

    def load(self):
        if not os.path.exists(REGISTRY_FILE):
            return {}
        try:
            with open(REGISTRY_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading local registry: {e}")
            return {}

    def save(self):
        with open(REGISTRY_FILE, "w") as f:
            json.dump(self.repos, f, indent=2)

    def add_repo(self, name, status="planned", role="product"):
        self.repos[name] = {
            "status": status,
            "role": role,
            "dependencies": [],
            "health": 1.0,
            "last_updated": datetime.now().isoformat()
        }
        self.save()

    def remove_repo(self, name):
        if name in self.repos:
            self.repos[name]["status"] = "deprecated"
            self.repos[name]["last_updated"] = datetime.now().isoformat()
            self.save()

    def update_repo(self, name, data):
        if name in self.repos:
            self.repos[name].update(data)
            self.repos[name]["last_updated"] = datetime.now().isoformat()
            self.save()
