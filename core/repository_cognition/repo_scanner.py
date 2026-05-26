import ast
import os
from pathlib import Path
from typing import List, Dict, Any
from core.observability.logger import dgm_logger

class CognitiveRepoScanner:
    def __init__(self, root_path: str = "."):
        self.root_path = Path(root_path)

    def scan(self) -> List[Dict[str, Any]]:
        dgm_logger.info(f"CognitiveRepoScanner: Scanning {self.root_path}")
        results = []
        for path in self.root_path.rglob("*"):
            if path.is_file():
                if path.suffix == ".py":
                    results.append(self._analyze_python(path))
                elif path.suffix in [".ts", ".js"]:
                    results.append(self._analyze_js_ts(path))
                elif path.suffix == ".rs":
                    results.append(self._analyze_rust(path))
                elif path.suffix == ".go":
                    results.append(self._analyze_go(path))
        return results

    def _analyze_python(self, path: Path) -> Dict[str, Any]:
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
            classes = [n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
            functions = [n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
            return {
                "path": str(path),
                "language": "python",
                "classes": classes,
                "functions": functions,
                "loc": len(path.read_text().splitlines())
            }
        except Exception as e:
            return {"path": str(path), "error": str(e)}

    def _analyze_js_ts(self, path: Path) -> Dict[str, Any]:
        # Simplified parser for JS/TS
        return {"path": str(path), "language": "javascript/typescript", "status": "scanned"}

    def _analyze_rust(self, path: Path) -> Dict[str, Any]:
        return {"path": str(path), "language": "rust", "status": "scanned"}

    def _analyze_go(self, path: Path) -> Dict[str, Any]:
        return {"path": str(path), "language": "go", "status": "scanned"}
