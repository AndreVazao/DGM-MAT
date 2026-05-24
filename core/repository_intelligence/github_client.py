import os
import requests
from typing import Tuple, Dict, Any, Optional

class GitHubClient:
    def __init__(self, token: Optional[str] = None, owner: Optional[str] = None):
        self.token = token or os.getenv("GITHUB_TOKEN")
        self.owner = owner or os.getenv("GITHUB_OWNER")
        self.api_url = "https://api.github.com"

    def create_repo(self, name: str, description: str = "", private: bool = False) -> Tuple[int, Dict[str, Any]]:
        url = f"{self.api_url}/user/repos"
        payload = {
            "name": name,
            "private": private,
            "auto_init": False, # We will push our own content
            "description": description or f"DGM-MAT ecosystem repo: {name}"
        }
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json"
        }
        r = requests.post(url, json=payload, headers=headers)
        return r.status_code, r.json()

    def get_repo(self, name: str) -> Tuple[int, Dict[str, Any]]:
        url = f"{self.api_url}/repos/{self.owner}/{name}"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json"
        }
        r = requests.get(url, headers=headers)
        return r.status_code, r.json()
