import os
import shutil
import subprocess  # nosec
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

from core.observability.logger import dgm_logger
from core.ecosystem.ecosystem_registry import EcosystemRegistry
from core.ecosystem.ecosystem_models import EcosystemNode, EcosystemRole, EcosystemStatus
from core.repository_intelligence.repo_classifier import classify_repo
from core.repository_intelligence.tech_detector import detect_tech_stack
from core.repository_intelligence.github_client import GitHubClient

class RepoImporter:
    def __init__(self, workspace_path: Path = Path("labs/external"), registry: Optional[EcosystemRegistry] = None):
        self.workspace_path = workspace_path
        self.registry = registry or EcosystemRegistry()
        self.workspace_path.mkdir(parents=True, exist_ok=True)
        self.github = GitHubClient()

    def _run_git(self, args: List[str], cwd: Path) -> subprocess.CompletedProcess:
        return subprocess.run(["git"] + args, cwd=cwd, capture_output=True, text=True)  # nosec

    def import_repo(self, repo_url: str, category_override: Optional[str] = None) -> Dict[str, Any]:
        repo_name = repo_url.split("/")[-1].replace(".git", "")
        target_path = self.workspace_path / repo_name

        dgm_logger.info(f"Importing repository: {repo_name} from {repo_url}")

        if target_path.exists():
            dgm_logger.warning(f"Repository {repo_name} already exists at {target_path}. Skipping clone.")
        else:
            dgm_logger.info(f"Cloning {repo_url} (depth 1)...")
            clone_res = subprocess.run(["git", "clone", "--depth", "1", repo_url, str(target_path)], capture_output=True, text=True)  # nosec
            if clone_res.returncode != 0:
                return {"status": "error", "message": f"Clone failed: {clone_res.stderr}"}

        # Setup GitHub Remote and Branch (v1 Engine logic)
        try:
            self._setup_git_remotes_and_branch(target_path, repo_name, repo_url)
        except Exception as e:
            dgm_logger.error(f"Failed to setup git remotes for {repo_name}: {e}")

        # Tech stack detection
        tech_stack = detect_tech_stack(target_path)

        # Classification
        if category_override:
            role_str = category_override.lower()
        else:
            role_str = classify_repo(target_path, tech_stack)

        # Cleanup sensitive files
        self._cleanup_sensitive_files(target_path)

        # Normalize README
        self._normalize_readme(target_path, repo_url, role_str)

        # Register in ecosystem
        try:
            role = EcosystemRole(role_str)
        except ValueError:
            role = EcosystemRole.EXTERNAL_LABS

        node = EcosystemNode(
            name=repo_name,
            role=role,
            status=EcosystemStatus.ACTIVE,
            description=f"Imported from {repo_url}",
            metadata={
                "source_url": repo_url,
                "import_date": datetime.now().isoformat(),
                "tech_stack": ",".join(tech_stack)
            }
        )
        self.registry.register_node(node)
        self.registry.save()

        return {
            "repo_name": repo_name,
            "classification": role_str,
            "path": str(target_path),
            "dependencies": tech_stack,
            "status": "cloned"
        }

    def _setup_git_remotes_and_branch(self, repo_path: Path, repo_name: str, upstream_url: str):
        # 1. Ensure GitHub repo exists
        status, _ = self.github.get_repo(repo_name)
        if status == 404:
            dgm_logger.info(f"Creating GitHub repo: {repo_name}")
            self.github.create_repo(repo_name)

        # 2. Setup remotes
        self._run_git(["remote", "remove", "origin"], cwd=repo_path)
        self._run_git(["remote", "add", "upstream", upstream_url], cwd=repo_path)

        github_owner = self.github.owner or "AndreVazao"
        origin_url = f"https://github.com/{github_owner}/{repo_name}.git"
        self._run_git(["remote", "add", "origin", origin_url], cwd=repo_path)

        # 3. Create external/import branch
        self._run_git(["checkout", "-b", "external/import"], cwd=repo_path)

        # 4. Push to origin
        dgm_logger.info(f"Pushing {repo_name} to {origin_url}...")
        push_res = self._run_git(["push", "-u", "origin", "external/import"], cwd=repo_path)
        if push_res.returncode != 0:
             dgm_logger.warning(f"Git push failed (expected in sandbox): {push_res.stderr}")

    def _cleanup_sensitive_files(self, repo_path: Path):
        sensitive_patterns = [".env", "*.key", "*.pem", "tokens.json", "credentials.json"]
        for pattern in sensitive_patterns:
            for p in repo_path.rglob(pattern):
                if p.is_file():
                    dgm_logger.info(f"Removing sensitive file: {p}")
                    p.unlink()

    def _normalize_readme(self, repo_path: Path, source_url: str, category: str):
        readme_path = repo_path / "README.md"
        header = f"# DGM-MAT Ecosystem Import: {repo_path.name}\n\n"
        header += f"- **Source**: [{source_url}]({source_url})\n"
        header += f"- **Category**: {category.upper()}\n"
        header += f"- **Import Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        header += "---\n\n"
        if readme_path.exists():
            try:
                content = readme_path.read_text(encoding="utf-8")
                readme_path.write_text(header + content, encoding="utf-8")
            except Exception as e:
                dgm_logger.error(f"Failed to normalize README for {repo_path.name}: {e}")
        else:
            readme_path.write_text(header + "Original README not found.", encoding="utf-8")
