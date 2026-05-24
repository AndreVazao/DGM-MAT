import os
import requests

class GitHubClient:
    def __init__(self):
        self.token = os.getenv("GITHUB_TOKEN")
        self.owner = os.getenv("GITHUB_OWNER")
        self.api_url = "https://api.github.com"

    def create_repo(self, name, description="", private=False):
        url = f"{self.api_url}/user/repos"
        payload = {
            "name": name,
            "private": private,
            "auto_init": True,
            "description": description or f"DGM-MAT ecosystem repo: {name}"
        }
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json"
        }
        r = requests.post(url, json=payload, headers=headers)
        return r.status_code, r.json()

    def get_repo(self, name):
        url = f"{self.api_url}/repos/{self.owner}/{name}"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json"
        }
        r = requests.get(url, headers=headers)
        return r.status_code, r.json()
