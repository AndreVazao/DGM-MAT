import os
import ast
import hashlib
from typing import List, Dict, Set, Optional
from pathlib import Path
from .migration_manifest import ModuleInventoryItem, ModuleCategory

class DependencyScanner:
    def __init__(self, base_dir: str = "."):
        self.base_dir = Path(base_dir).resolve()

    def scan_file(self, file_path: Path) -> Optional[ModuleInventoryItem]:
        if not file_path.suffix == ".py":
            return None

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                tree = ast.parse(content)
        except (UnicodeDecodeError, SyntaxError):
            return None

        rel_path = str(file_path.relative_to(self.base_dir)).replace("\\", "/")
        dependencies = self._extract_imports(tree, rel_path)

        return ModuleInventoryItem(
            path=rel_path,
            dependency_count=len(dependencies),
            file_size=file_path.stat().st_size,
            dependencies=list(dependencies),
            hash=self._compute_hash(content)
        )

    def _extract_imports(self, tree: ast.AST, current_file: str) -> Set[str]:
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    normalized = self._normalize_import(alias.name)
                    if normalized:
                        imports.add(normalized)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    normalized = self._normalize_import(node.module)
                    if normalized:
                        imports.add(normalized)
        return imports

    def _normalize_import(self, module_name: str) -> Optional[str]:
        # We only care about internal imports (core, shared, cockpit, etc.)
        internal_roots = ["core", "shared", "cockpit", "tools", "scripts"]
        parts = module_name.split('.')
        if parts[0] in internal_roots:
            # Try to resolve to a file path
            potential_path = module_name.replace('.', '/') + ".py"
            if (self.base_dir / potential_path).exists():
                return potential_path

            # Try to resolve to a directory (__init__.py)
            potential_dir = module_name.replace('.', '/') + "/__init__.py"
            if (self.base_dir / potential_dir).exists():
                return potential_dir

            return potential_path # Return anyway as a reference
        return None

    def _compute_hash(self, content: str) -> str:
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def scan_tree(self) -> Dict[str, ModuleInventoryItem]:
        inventory = {}
        for root, _, files in os.walk(self.base_dir):
            if any(excluded in root for excluded in [".git", ".runtime", "__pycache__", "node_modules", "venv", ".venv", "dist", "build"]):
                continue

            for file in files:
                if file.endswith(".py"):
                    full_path = Path(root) / file
                    item = self.scan_file(full_path)
                    if item:
                        inventory[item.path] = item

        # Second pass: calculate import_count (dependents)
        for path, item in inventory.items():
            for dep in item.dependencies:
                if dep in inventory:
                    inventory[dep].import_count += 1
                    if path not in inventory[dep].dependents:
                        inventory[dep].dependents.append(path)

        return inventory
