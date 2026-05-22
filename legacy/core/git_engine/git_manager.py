import subprocess
import os
from typing import List, Dict, Any, Optional
from core.event_bus.bus import Event, EventBus

class GitManager:
    def __init__(self, event_bus: EventBus, root_path: str = "."):
        self.bus = event_bus
        self.root_path = root_path

    def _run_git(self, args: List[str]) -> str:
        try:
            result = subprocess.run(
                ["git"] + args,
                cwd=self.root_path,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            self._log_error(f"Git command failed: {' '.join(args)}", str(e.stderr))
            raise

    def create_branch(self, branch_name: str):
        self._run_git(["checkout", "-b", branch_name])
        self._publish_event("branch_created", {"branch": branch_name})

    def commit(self, message: str, files: List[str] = ["."]):
        for f in files:
            self._run_git(["add", f])
        self._run_git(["commit", "-m", message])
        self._publish_event("commit_generated", {"message": message, "files": files})

    def get_diff(self, target: str = "HEAD") -> str:
        return self._run_git(["diff", target])

    def create_pull_request(self, title: str, body: str, head: str, base: str = "main"):
        # Simulated PR generation (logging event)
        self._publish_event("pull_request_generated", {
            "title": title,
            "body": body,
            "head": head,
            "base": base
        })

    def rollback(self, commit_hash: str):
        self._run_git(["reset", "--hard", commit_hash])
        self._publish_event("rollback_executed", {"commit": commit_hash})

    def _publish_event(self, event_type: str, payload: Dict[str, Any]):
        self.bus.publish(Event(
            source="git_engine",
            type=event_type,
            payload=payload,
            priority="high"
        ))

    def _log_error(self, message: str, detail: str):
        self.bus.publish(Event(
            source="git_engine",
            type="error",
            payload={"message": message, "detail": detail},
            priority="critical"
        ))
