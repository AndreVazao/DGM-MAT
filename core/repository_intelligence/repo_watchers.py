import time
import threading
from pathlib import Path
from typing import List, Dict, Any, Callable
from core.observability.logger import dgm_logger

class RepoWatcher:
    """
    Monitors repositories for changes and triggers re-analysis.
    """
    def __init__(self, repos_path: str, callback: Callable):
        self.repos_path = Path(repos_path)
        self.callback = callback
        self.watched_repos: Dict[str, float] = {}
        self._running = False
        self._thread = None

    def start(self):
        self._running = True
        self._thread = threading.Thread(target=self._watch_loop, daemon=True)
        self._thread.start()
        dgm_logger.info(f"RepoWatcher: Monitoring {self.repos_path}")

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)

    def _watch_loop(self):
        while self._running:
            try:
                self._scan_repos()
            except Exception as e:
                dgm_logger.error(f"RepoWatcher: Error during scan: {e}")
            time.sleep(60) # Polling interval

    def _scan_repos(self):
        if not self.repos_path.exists():
            return

        for repo_dir in self.repos_path.iterdir():
            if not repo_dir.is_dir():
                continue

            # Simple check for modified time of the directory (not recursive for performance)
            # In a real system, we'd use watchdog or check git head
            mtime = repo_dir.stat().st_mtime
            repo_name = repo_dir.name

            if repo_name not in self.watched_repos:
                self.watched_repos[repo_name] = mtime
                dgm_logger.info(f"RepoWatcher: Now watching {repo_name}")
                continue

            if mtime > self.watched_repos[repo_name]:
                dgm_logger.info(f"RepoWatcher: Detected change in {repo_name}. Triggering callback.")
                self.watched_repos[repo_name] = mtime
                self.callback(repo_name, repo_dir)

    def health(self) -> Dict[str, Any]:
        return {
            "watched_count": len(self.watched_repos),
            "is_running": self._running
        }
