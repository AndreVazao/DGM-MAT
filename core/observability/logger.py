from loguru import logger
import sys
import os
from pathlib import Path

# Remove default handler
logger.remove()

# 1. Console Logging
logger.add(
    sys.stdout,
    colorize=True,
    format=(
        "<green>{time:HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    ),
    level="INFO"
)

# 2. Persistent File Logging (Canonical path Requirement 7)
try:
    if os.name == 'nt':
        log_dir = Path("C:/DevopGodMode/runtime/logs")
    else:
        # Fallback to local project dir for non-Windows or if env var not set
        project_root = Path(__file__).parent.parent.parent
        log_dir = project_root / "runtime" / "logs"

    log_dir.mkdir(parents=True, exist_ok=True)

    log_file = log_dir / "dgm-runtime.log"

    logger.add(
        str(log_file),
        rotation="10 MB",
        retention="1 week",
        compression="zip",
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
        level="DEBUG",
        encoding="utf-8"
    )

    # Also log startup to file
    logger.info(f"Logger: Initialized persistent logging at {log_file}")
except Exception as e:
    # Silent fallback to stdout if file logging fails (e.g. permissions)
    print(f"Logger: Warning - Could not initialize file logging: {e}")

dgm_logger = logger
