"""Small, Qt-independent client for reading one durable mission checkpoint."""
from __future__ import annotations

from typing import Any, Callable


def fetch_mission_checkpoint(
    api_url: str,
    mission_id: str,
    *,
    request: Callable[..., Any],
) -> dict[str, Any] | None:
    """Fetch one mission by ID; never enumerate the full mission collection."""
    response = request(
        "GET",
        f"/missions/{mission_id}",
        timeout=(2, 8),
    )
    if response.status_code == 404:
        return None
    if response.status_code != 200:
        raise RuntimeError(
            f"Não foi possível consultar a missão {mission_id} "
            f"(HTTP {response.status_code})."
        )
    data = response.json()
    if not isinstance(data, dict) or data.get("mission_id") != mission_id:
        raise ValueError("O runtime devolveu um checkpoint de missão inválido.")
    return data
