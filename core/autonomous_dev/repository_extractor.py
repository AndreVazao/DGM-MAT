import os
import shutil
import json
import ast
import logging
from typing import List, Dict, Set, Optional
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class RepositoryExtractor:
    def __init__(self, manifest_path: str, base_dir: str = "."):
        self.manifest_path = manifest_path
        self.base_dir = Path(base_dir).resolve()
        self.manifest = self._load_manifest()
        self.report_dir = self.base_dir / "reports" / "extraction"
        self.report_dir.mkdir(parents=True, exist_ok=True)

        self.dest_map = {
            "runtime": "../DGM-MAT-Runtime",
            "providers": "../DGM-MAT-Providers",
            "memory": "../DGM-MAT-Memory",
            "cockpit": "../DGM-MAT-Cockpit"
        }

    def _load_manifest(self) -> Dict[str, List[str]]:
        with open(self.manifest_path, 'r') as f:
            return json.load(f)

    def extract(self, component: str, dry_run: bool = False) -> bool:
        if component not in self.manifest:
            logger.error(f"Component '{component}' not found in manifest.")
            return False

        modules = self.manifest[component]
        dest_root = (self.base_dir / self.dest_map[component]).resolve()

        logger.info(f"Starting extraction for {component} to {dest_root}")
        if dry_run:
            logger.info("DRY RUN MODE ENABLED - No files will be copied.")

        migration_report = {
            "component": component,
            "destination": str(dest_root),
            "modules": [],
            "files_copied": [],
            "errors": []
        }

        rollback_manifest = {
            "component": component,
            "files_to_remove": []
        }

        all_extracted_paths = set()
        for mod in modules:
            source_path = self.base_dir / mod
            if not source_path.exists():
                err = f"Source module {mod} does not exist."
                logger.warning(err)
                migration_report["errors"].append(err)
                continue

            all_extracted_paths.add(mod)

        # Copy files
        for mod in modules:
            source_path = self.base_dir / mod
            if not source_path.exists():
                continue

            if source_path.is_dir():
                for root, dirs, files in os.walk(source_path):
                    rel_root = os.path.relpath(root, self.base_dir)
                    dest_dir = dest_root / rel_root

                    if not dry_run:
                        dest_dir.mkdir(parents=True, exist_ok=True)

                    for file in files:
                        src_file = Path(root) / file
                        rel_file = os.path.relpath(src_file, self.base_dir)
                        dst_file = dest_root / rel_file

                        migration_report["files_copied"].append(rel_file)
                        rollback_manifest["files_to_remove"].append(rel_file)

                        if not dry_run:
                            dst_file.parent.mkdir(parents=True, exist_ok=True)
                            shutil.copy2(src_file, dst_file)
            else:
                rel_file = os.path.relpath(source_path, self.base_dir)
                dst_file = dest_root / rel_file
                migration_report["files_copied"].append(rel_file)
                rollback_manifest["files_to_remove"].append(rel_file)

                if not dry_run:
                    dst_file.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source_path, dst_file)

        # Detect broken imports
        broken_imports = self.detect_broken_imports(component, migration_report["files_copied"])

        # Save reports
        if not dry_run:
            self._save_json(self.report_dir / "migration_report.json", migration_report)
            self._save_json(self.report_dir / "rollback_manifest.json", rollback_manifest)
            self._save_json(self.report_dir / "broken_imports.json", broken_imports)

        logger.info(f"Extraction for {component} completed.")
        return True

    def detect_broken_imports(self, component: str, copied_files: List[str]) -> Dict[str, List[str]]:
        broken = {}
        extracted_modules = set(self.manifest[component])

        # Helper to check if a module is "internal" to the extraction
        def is_internal(module_path: str) -> bool:
            for ext in extracted_modules:
                if module_path.startswith(ext.replace('/', '.')):
                    return True
            return False

        for rel_file in copied_files:
            if not rel_file.endswith('.py'):
                continue

            abs_path = self.base_dir / rel_file
            if not abs_path.exists():
                continue

            with open(abs_path, 'r', encoding='utf-8') as f:
                try:
                    tree = ast.parse(f.read())
                except SyntaxError:
                    continue

            file_broken = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if self._is_external_dependency(alias.name) and not is_internal(alias.name):
                            file_broken.append(f"Import {alias.name}")
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        full_module = node.module
                        if self._is_external_dependency(full_module) and not is_internal(full_module):
                            file_broken.append(f"From {full_module} import ...")

            if file_broken:
                broken[rel_file] = file_broken

        return broken

    def _is_external_dependency(self, module_name: str) -> bool:
        # Simple check: if it starts with core, shared, or cockpit, it's ours.
        # If it doesn't, it might be a standard lib or installed package (which we assume stay available).
        ours = ["core", "shared", "cockpit"]
        for o in ours:
            if module_name.startswith(o):
                return True
        return False

    def _save_json(self, path: Path, data: Dict):
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)
