import ast
import os
import time
from pathlib import Path
from typing import List, Dict, Any, Set
from core.observability.logger import dgm_logger

class CognitiveRepoScanner:
    def __init__(self, root_path: str = "."):
        self.root_path = Path(root_path)
        self.exclusions = {".runtime", ".git", "__pycache__", "node_modules", "dist", "build", ".venv"}

    def scan(self, max_files: int = 2000, timeout_seconds: float = 10.0) -> List[Dict[str, Any]]:
        dgm_logger.info(f"CognitiveRepoScanner: Scanning {self.root_path}")
        results = []
        started = time.monotonic()
        try:
            for path in self.root_path.rglob("*"):
                if len(results) >= max_files:
                    dgm_logger.warning(f"CognitiveRepoScanner: file limit reached ({max_files})")
                    break
                if time.monotonic() - started >= timeout_seconds:
                    dgm_logger.warning(f"CognitiveRepoScanner: timeout reached ({timeout_seconds}s)")
                    break
                try:
                    # Skip excluded directories and their contents
                    if any(part in self.exclusions for part in path.parts):
                        continue

                    if path.is_file():
                        if path.suffix == ".py":
                            results.append(self._analyze_python(path))
                        elif path.suffix in [".ts", ".js"]:
                            results.append(self._analyze_js_ts(path))
                        elif path.suffix == ".rs":
                            results.append(self._analyze_rust(path))
                        elif path.suffix == ".go":
                            results.append(self._analyze_go(path))
                except (PermissionError, OSError):
                    # Requirement 8: Prevent Windows access denied errors
                    continue
        except Exception as e:
            dgm_logger.error(f"CognitiveRepoScanner: Fatal error during scan: {e}")

        return results

    def _analyze_python(self, path: Path) -> Dict[str, Any]:
        try:
            content = path.read_text(encoding="utf-8")
            tree = ast.parse(content)
            classes = [n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
            functions = [n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
            return {
                "path": str(path),
                "language": "python",
                "classes": classes,
                "functions": functions,
                "loc": len(content.splitlines())
            }
        except Exception as e:
            return {"path": str(path), "error": str(e)}

    def _analyze_js_ts(self, path: Path) -> Dict[str, Any]:
        return {"path": str(path), "language": "javascript/typescript", "status": "scanned"}

    def _analyze_rust(self, path: Path) -> Dict[str, Any]:
        return {"path": str(path), "language": "rust", "status": "scanned"}

    def _analyze_go(self, path: Path) -> Dict[str, Any]:
        return {"path": str(path), "language": "go", "status": "scanned"}
