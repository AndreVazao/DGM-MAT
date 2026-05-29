from loguru import logger
import sys
from pathlib import Path

logger.remove()

logger.add(
    sys.stdout,
    colorize=True,
    format=(
        "<green>{time:HH:mm:ss}</green> | "
        "<level>{level}</level> | "
        "{message}"
    ),
)

try:
    log_dir = Path("C:/DevopGodMode/runtime/logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    logger.add(
        log_dir / "dgm-runtime.log",
        rotation="5 MB",
        retention=5,
        encoding="utf-8",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
    )
except Exception:
    pass

dgm_logger = logger
