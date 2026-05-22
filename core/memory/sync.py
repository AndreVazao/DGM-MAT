import os
import shutil
from typing import List

class MemorySync:
    def __init__(self, core_memory_path: str = "core/memory/storage", andreos_path: str = "AndreOS"):
        self.core_memory_path = core_memory_path
        self.andreos_path = andreos_path
        os.makedirs(self.andreos_path, exist_ok=True)

    def sync_to_andreos(self) -> List[str]:
        """Sync all snapshots from core memory to AndreOS (Long-Term Memory)."""
        snapshots_src = os.path.join(self.core_memory_path, "snapshots")
        if not os.path.exists(snapshots_src):
            return []

        synced_files = []
        for filename in os.listdir(snapshots_src):
            src_file = os.path.join(snapshots_src, filename)
            dest_file = os.path.join(self.andreos_path, filename)

            # Append-only: copy if it doesn't exist in destination
            if not os.path.exists(dest_file):
                shutil.copy2(src_file, dest_file)
                synced_files.append(filename)

        return synced_files

    def check_consistency(self) -> bool:
        """Verify that all core snapshots are present in AndreOS."""
        snapshots_src = os.path.join(self.core_memory_path, "snapshots")
        if not os.path.exists(snapshots_src):
            return True

        for filename in os.listdir(snapshots_src):
            dest_file = os.path.join(self.andreos_path, filename)
            if not os.path.exists(dest_file):
                return False
        return True
