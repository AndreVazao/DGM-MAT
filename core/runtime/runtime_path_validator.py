from pathlib import Path
from typing import Dict, Any

from core.observability.logger import dgm_logger


class RuntimePathValidator:
    REQUIRED_PATHS = [
        Path("C:/DevopGodMode/storage"),
        Path("C:/DevopGodMode/config"),
        Path("C:/DevopGodMode/runtime"),
        Path("C:/ProgramasGodMode/andreos-memory"),
    ]

    def validate(self, ensure: bool = True) -> Dict[str, Dict[str, Any]]:
        results: Dict[str, Dict[str, Any]] = {}
        for path in self.REQUIRED_PATHS:
            try:
                if ensure:
                    path.mkdir(parents=True, exist_ok=True)

                exists = path.exists()
                results[str(path)] = {
                    "path": str(path),
                    "exists": exists,
                    "is_dir": path.is_dir() if exists else False,
                }
            except Exception as exc:
                dgm_logger.warning(f"RuntimePathValidator: Path validation failed for {path}: {exc}")
                results[str(path)] = {
                    "path": str(path),
                    "exists": False,
                    "is_dir": False,
                    "error": str(exc),
                }
        return results

    def is_valid(self, results: Dict[str, Dict[str, Any]]) -> bool:
        return all(item.get("exists") and item.get("is_dir") for item in results.values())
