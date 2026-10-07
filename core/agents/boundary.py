"""Public Core -> DGM-MAT-Agents composition boundary."""
from __future__ import annotations

import os
import sys
from pathlib import Path


def _agents_src() -> Path:
    configured = os.getenv("DGM_AGENTS_PATH")
    if configured:
        return Path(configured).expanduser().resolve()
    return Path(__file__).resolve().parents[3] / "DGM-MAT-Agents" / "src"


def _ensure_agents_importable() -> None:
    src = _agents_src()
    if not src.exists():
        raise RuntimeError(f"DGM-MAT-Agents source not found: {src}")
    value = str(src)
    if value not in sys.path:
        sys.path.insert(0, value)


def create_runtime_agents():
    _ensure_agents_importable()
    from dgm_mat_agents import AutonomyAgent, ProviderAgent, RepoAgent
    from core.agents.service_adapters import (
        CoreLoggerAdapter,
        CoreProviderServiceAdapter,
        CoreTaskServiceAdapter,
    )

    logger = CoreLoggerAdapter()
    return {
        "repo": RepoAgent("repo-agent", logger=logger),
        "provider": ProviderAgent(
            "provider-agent",
            logger=logger,
            provider_service=CoreProviderServiceAdapter(),
        ),
        "autonomy": AutonomyAgent(
            "autonomy-agent",
            logger=logger,
            task_service=CoreTaskServiceAdapter(),
        ),
    }
