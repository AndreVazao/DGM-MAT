import os
import requests
import json

OWNER = os.getenv("GITHUB_OWNER")
TOKEN = os.getenv("GITHUB_TOKEN")

ACTION = os.getenv("ACTION")
REPOS = os.getenv("REPOS", "")
DESCRIPTION = os.getenv("DESCRIPTION", "")
VISIBILITY = os.getenv("VISIBILITY", "public")

API = "https://api.github.com"

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github+json"
}


def parse_repos():
    if not REPOS:
        return []
    return [r.strip() for r in REPOS.split(",") if r.strip()]


def create_repo(name):
    url = f"{API}/user/repos"

    payload = {
        "name": name,
        "description": DESCRIPTION or f"DGM-MAT ecosystem repo: {name}",
        "private": VISIBILITY != "public",
        "auto_init": True
    }

    r = requests.post(url, json=payload, headers=HEADERS)

    if r.status_code == 201:
        print(f"[CREATED] {name}")
    else:
        print(f"[ERROR] {name} -> {r.text}")


def update_repo(name):
    url = f"{API}/repos/{OWNER}/{name}"

    payload = {}

    if DESCRIPTION:
        payload["description"] = DESCRIPTION

    r = requests.patch(url, json=payload, headers=HEADERS)

    print(f"[UPDATED] {name} -> {r.status_code}")


def deprecate_repo(name):
    # safe soft deprecate via description tag
    url = f"{API}/repos/{OWNER}/{name}"

    current_desc = ""
    r_get = requests.get(url, headers=HEADERS)
    if r_get.status_code == 200:
        current_desc = r_get.json().get("description", "") or ""

    if not current_desc.startswith("[DEPRECATED]"):
        payload = {
            "description": f"[DEPRECATED] {current_desc} {DESCRIPTION}".strip()
        }
        r = requests.patch(url, json=payload, headers=HEADERS)
        print(f"[DEPRECATED] {name} -> {r.status_code}")
    else:
        print(f"[ALREADY DEPRECATED] {name}")


def list_repos():
    url = f"{API}/users/{OWNER}/repos"
    r = requests.get(url, headers=HEADERS)

    if r.status_code == 200:
        for repo in r.json():
            print(f"{repo['name']} | {'private' if repo['private'] else 'public'} | {repo['updated_at']}")
    else:
        print(f"[ERROR LISTING] {r.text}")


def main():
    repos = parse_repos()

    print(f"\nACTION: {ACTION}\n")

    if ACTION == "list":
        list_repos()
        return

    if not repos:
        print("No repos provided.")
        return

    for repo in repos:
        if ACTION == "create":
            create_repo(repo)
        elif ACTION == "update":
            update_repo(repo)
        elif ACTION == "deprecate":
            deprecate_repo(repo)


if __name__ == "__main__":
    main()
