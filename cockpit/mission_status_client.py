"""Small, Qt-independent client for reading one durable mission checkpoint."""
from __future__ import annotations

from typing import Any, Callable

import requests
import time


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


def submit_mission_once(
    request: Callable[..., Any],
    directive: str,
) -> dict[str, Any]:
    """Submit exactly one mission POST; callers must not retry an ambiguous timeout."""
    response = request(
        "POST",
        "/missions",
        json={
            "goal": directive,
            "description": "Pedido enviado pelo cockpit de chat",
        },
        timeout=(2, 10),
    )
    if response.status_code not in (200, 201):
        raise RuntimeError(
            f"O runtime recusou o pedido (HTTP {response.status_code}). Não foi assumido sucesso."
        )
    data = response.json()
    if not isinstance(data, dict) or data.get("status") != "success" or not data.get("mission_id"):
        error = data.get("error") if isinstance(data, dict) else None
        raise RuntimeError(
            f"O pedido não foi aceite. {error or 'Resposta sem confirmação de criação.'}"
        )
    return data


def wait_for_mission_checkpoint(
    mission_id: str,
    fetch_checkpoint: Callable[[str], dict[str, Any] | None],
    *,
    timeout_seconds: int = 65,
    poll_interval: float = 2.0,
    monotonic: Callable[[], float] = time.monotonic,
    sleep: Callable[[float], None] = time.sleep,
) -> dict[str, Any] | None:
    """Poll only one mission ID; temporary GET timeouts never resubmit the mission."""
    deadline = monotonic() + timeout_seconds
    terminal = {
        "COMPLETED", "FAILED", "CANCELLED",
        "WAITING_FOR_USER", "APPROVAL_PENDING",
    }
    while monotonic() < deadline:
        try:
            mission = fetch_checkpoint(mission_id)
        except requests.Timeout:
            sleep(poll_interval)
            continue
        if mission is None:
            raise RuntimeError(
                f"A missão {mission_id} ainda não aparece na consulta do runtime."
            )
        status = str(mission.get("status", "UNKNOWN")).upper()
        action_status = str(mission.get("action_status") or "").upper()
        if status in terminal or (status == "QUEUED" and action_status == "QUEUED"):
            return mission
        sleep(poll_interval)
    return None
