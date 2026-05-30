import os
import shutil
from pathlib import Path
from typing import List
from .migration_manifest import MigrationPlan, MigrationPlanItem
from .import_rewriter import ImportRewriter

class ModuleExporter:
    def __init__(self, target_root: str = "../DGM-MAT-Core", base_dir: str = "."):
        self.target_root = Path(target_root).resolve()
        self.base_dir = Path(base_dir).resolve()
        self.rewriter = ImportRewriter()

    def export_plan(self, plan: MigrationPlan) -> bool:
        if not self.target_root.exists():
            self.target_root.mkdir(parents=True, exist_ok=True)

        success = True
        for item in plan.items:
            try:
                if not self.export_item(item):
                    success = False
                    item.status = "FAILED"
                else:
                    item.status = "COMPLETED"
            except Exception as e:
                print(f"Error exporting {item.source_path}: {e}")
                item.status = f"ERROR: {str(e)}"
                success = False
        return success

    def export_item(self, item: MigrationPlanItem) -> bool:
        src = self.base_dir / item.source_path
        dst = self.target_root / item.target_path

        if not src.exists():
            return False

        dst.parent.mkdir(parents=True, exist_ok=True)

        if src.is_file():
            if src.suffix == ".py":
                with open(src, "r", encoding="utf-8") as f:
                    content = f.read()

                rewritten = self.rewriter.rewrite_content(content)

                with open(dst, "w", encoding="utf-8") as f:
                    f.write(rewritten)
            else:
                shutil.copy2(src, dst)
            return True
        return False
