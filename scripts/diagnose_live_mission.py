#!/usr/bin/env python3
"""Submit one bounded read-only mission through the PC-local DGM-MAT API.

The script never prints or persists bearer tokens. It accepts only intents in
the runtime's read-only auto-run allowlist, checks that the queue worker is live,
and polls the durable checkpoint. It never calls an approval endpoint, retries,
restarts the runtime, or changes host configuration.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from core.autonomy.mission_intent_router import classify_mission_intent
from urllib.parse import urlparse
from urllib.request import Request, urlopen

TERMINAL = {"COMPLETED", "FAILED", "CANCELLED"}
LOOPBACK_NAMES = {"127.0.0.1", "localhost", "::1"}

# Keep aligned with MissionEngine.AUTO_RUN_READ_ONLY_INTENTS. The runtime remains
# the authority: the script additionally verifies that its new action was
# actually auto-approved before it reports a dispatch.
READ_ONLY_AUTO_RUN_INTENTS = frozenset({
    "list_repositories",
    "architecture_summary",
    "repository_status",
    "local_research",
    "system_summary",
    "engines_inventory",
    "ollama_status",
    "claude_status",
})


def validate_mission_goal(goal: str):
    """Fail closed unless the goal maps to a supported read-only auto-run intent."""
    decision = classify_mission_intent(goal)
    if (
        not decision.supported
        or decision.requires_approval
        or decision.intent not in READ_ONLY_AUTO_RUN_INTENTS
    ):
        raise ValueError(
            "Mission goal is not in the read-only auto-run allowlist; "
            "no mission will be submitted."
        )
    return decision


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def default_report_dir() -> Path:
    local_app_data = os.getenv("LOCALAPPDATA")
    if local_app_data:
        return Path(local_app_data) / "DGM-MAT" / "diagnostics"
    return Path.home() / ".dgm-mat" / "diagnostics"


def bootstrap_path() -> Path:
    override = os.getenv("DGM_LOCAL_BOOTSTRAP_FILE")
    if override:
        return Path(override)
    local_app_data = os.getenv("LOCALAPPDATA")
    if not local_app_data:
        raise RuntimeError("LOCALAPPDATA is not set and DGM_LOCAL_BOOTSTRAP_FILE was not supplied.")
    return Path(local_app_data) / "DGM-MAT" / "security" / "bootstrap.token"


def validate_base_url(value: str) -> str:
    parsed = urlparse(value)
    if parsed.scheme != "http" or parsed.hostname not in LOOPBACK_NAMES:
        raise ValueError("Only local loopback HTTP URLs are allowed.")
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError("Base URL must not contain credentials, query or fragment.")
    if parsed.path not in ("", "/"):
        raise ValueError("Base URL must be an origin only, without a path.")
    return value.rstrip("/")


def request_json(base_url: str, path: str, *, method: str = "GET",
                 payload: dict | None = None, bearer: str | None = None,
                 timeout: float = 5.0) -> tuple[int, dict | list | str]:
    headers = {"Accept": "application/json"}
    data = None
    if payload is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    if bearer:
        headers["Authorization"] = f"Bearer {bearer}"
    req = Request(base_url + path, data=data, headers=headers, method=method)
    try:
        with urlopen(req, timeout=timeout) as response:
            raw = response.read(1_000_000).decode("utf-8", errors="replace")
            status = response.status
    except HTTPError as exc:
        raw = exc.read(100_000).decode("utf-8", errors="replace")
        status = exc.code
    except (URLError, TimeoutError, OSError) as exc:
        raise RuntimeError(f"{method} {path} failed: {type(exc).__name__}: {exc}") from exc
    try:
        parsed = json.loads(raw) if raw else {}
    except json.JSONDecodeError:
        parsed = raw[:4000]
    return status, parsed


def safe_excerpt(value, limit: int = 16000):
    try:
        encoded = json.dumps(value, ensure_ascii=False, default=str)
    except (TypeError, ValueError):
        encoded = str(value)
    if len(encoded) <= limit:
        return value
    return {"truncated": True, "preview": encoded[:limit]}


def mission_checkpoint_status(mission: dict) -> str:
    """Return the explicit status even when the checkpoint payload is truncated."""
    status = mission.get("last_checkpoint_status")
    if isinstance(status, str) and status:
        return status
    checkpoint = mission.get("last_checkpoint")
    if isinstance(checkpoint, dict) and isinstance(checkpoint.get("status"), str):
        return checkpoint["status"]
    return "checkpoint unavailable"


def run(args: argparse.Namespace) -> tuple[int, dict]:
    report: dict = {
        "schema": "dgm-mat-live-mission-diagnostic.v1",
        "started_at": utc_now(),
        "finished_at": None,
        "base_url": args.base_url,
        "test_scope": "single read-only mission from the runtime auto-run allowlist",
        "goal": args.goal,
        "overall": "BLOCKED",
        "checks": {},
        "mission": None,
        "notes": [
            "HTTP /health only proves that the API process responds.",
            "Mission creation is not mission completion.",
            "The client never calls an approval endpoint; only the runtime's read-only allowlist can auto-approve.",
            "Unsupported or approval-required goals are rejected before mission creation.",
            "Bearer credentials are never written to this report.",
        ],
    }
    try:
        intent_decision = validate_mission_goal(args.goal)
        report["mission_intent"] = intent_decision.to_dict()

        base_url = validate_base_url(args.base_url)
        report["base_url"] = base_url

        code, health = request_json(base_url, "/health", timeout=args.request_timeout)
        report["checks"]["process_health"] = {
            "http_status": code,
            "passed": code == 200 and isinstance(health, dict) and health.get("status") == "healthy",
            "response": safe_excerpt(health, 3000),
        }
        if not report["checks"]["process_health"]["passed"]:
            raise RuntimeError("The public /health endpoint did not return a healthy response.")

        secret_path = bootstrap_path()
        report["checks"]["bootstrap_credential"] = {
            "path": str(secret_path),
            "exists": secret_path.is_file(),
        }
        if not secret_path.is_file():
            raise RuntimeError("Bootstrap token file is missing; no mission was submitted.")
        bootstrap_token = secret_path.read_text(encoding="utf-8")
        if not bootstrap_token or len(bootstrap_token) < 60 or bootstrap_token != bootstrap_token.strip():
            bootstrap_token = None
            raise RuntimeError("Bootstrap token file is empty or malformed; no mission was submitted.")
        report["checks"]["bootstrap_credential"]["valid_format"] = True

        status, session = request_json(
            base_url, "/auth/session", method="POST",
            payload={"client_id": "local-diagnostic"},
            bearer=bootstrap_token, timeout=args.request_timeout,
        )
        bootstrap_token = None
        report["checks"]["session_exchange"] = {
            "http_status": status,
            "passed": status == 201 and isinstance(session, dict)
                      and isinstance(session.get("access_token"), str)
                      and session.get("token_type") == "Bearer",
            "detail": session.get("detail") if isinstance(session, dict) else "Unexpected response shape",
        }
        if not report["checks"]["session_exchange"]["passed"]:
            raise RuntimeError("Local session exchange failed; no mission was submitted.")
        session_token = session["access_token"]
        session_scopes = session.get("scopes", [])

        status, runtime_health = request_json(
            base_url, "/runtime/health", bearer=session_token, timeout=args.request_timeout,
        )
        report["checks"]["runtime_health"] = {
            "http_status": status,
            "passed": status == 200,
            "response": safe_excerpt(runtime_health, 4000),
        }
        if status != 200:
            raise RuntimeError("Authenticated runtime-health request failed; no mission was submitted.")
        if not {"local-client", "operator"}.issubset(set(session_scopes)):
            raise RuntimeError("Local session lacks the required operator scopes; no mission was submitted.")

        status, telemetry = request_json(
            base_url, "/runtime/office/telemetry", bearer=session_token,
            timeout=args.request_timeout,
        )
        queue_health = telemetry.get("queue_worker", {}) if isinstance(telemetry, dict) else {}
        worker_alive = queue_health.get("worker_alive") is True
        report["checks"]["queue_worker"] = {
            "http_status": status,
            "passed": status == 200 and worker_alive,
            "details": safe_excerpt(queue_health, 2000),
        }
        if not report["checks"]["queue_worker"]["passed"]:
            raise RuntimeError("Mission queue worker is not confirmed alive; no mission was submitted.")

        status, created = request_json(
            base_url, "/runtime/missions", method="POST",
            payload={"goal": args.goal, "description": args.description},
            bearer=session_token, timeout=args.request_timeout,
        )
        report["checks"]["mission_submission"] = {
            "http_status": status,
            "passed": status == 200 and isinstance(created, dict)
                      and created.get("status") == "success"
                      and isinstance(created.get("mission_id"), str),
            "response": safe_excerpt(created, 4000),
        }
        if not report["checks"]["mission_submission"]["passed"]:
            raise RuntimeError("Mission submission failed; inspect the recorded HTTP response.")

        mission_id = created["mission_id"]
        report["mission"] = {
            "mission_id": mission_id,
            "goal": args.goal,
            "intent": intent_decision.to_dict(),
            "accepted_at": utc_now(),
            "initial_status": created.get("mission_status"),
            "initial_action_status": created.get("action_status"),
            "last_checkpoint": None,
            "poll_count": 0,
            "terminal": False,
        }
        if created.get("action_status") not in {"APPROVED", "RUNNING", "COMPLETED"}:
            report["overall"] = "BLOCKED"
            report["mission"]["conclusion"] = (
                "The runtime did not auto-approve this read-only mission. "
                "No manual approval or retry was attempted."
            )
            return 2, report

        deadline = time.monotonic() + args.poll_timeout
        last_detail = None
        while time.monotonic() < deadline:
            status, detail = request_json(
                base_url, f"/runtime/missions/{mission_id}",
                bearer=session_token, timeout=args.request_timeout,
            )
            report["mission"]["poll_count"] += 1
            if status != 200 or not isinstance(detail, dict):
                report["mission"]["last_checkpoint"] = {
                    "http_status": status,
                    "response": safe_excerpt(detail, 4000),
                }
                break
            last_detail = detail
            mission_status = detail.get("status")
            report["mission"]["last_checkpoint_status"] = mission_status
            report["mission"]["last_checkpoint"] = safe_excerpt(detail, 16000)
            if mission_status in TERMINAL:
                report["mission"]["terminal"] = True
                break
            if mission_status == "APPROVAL_PENDING":
                report["mission"]["approval_required"] = True
            time.sleep(args.poll_interval)

        if last_detail is not None:
            state = last_detail.get("status")
            if state == "COMPLETED":
                report["overall"] = "PASS"
                report["mission"]["conclusion"] = "Mission reached COMPLETED; review result/output in report."
            elif state in {"FAILED", "CANCELLED"}:
                report["overall"] = "FAIL"
                report["mission"]["conclusion"] = f"Mission reached terminal state {state}."
            else:
                report["overall"] = "BLOCKED"
                report["mission"]["conclusion"] = (
                    f"Mission did not reach a terminal state before timeout; latest state={state!r}. "
                    "No approval or retry was attempted."
                )
        else:
            report["overall"] = "BLOCKED"
            report["mission"]["conclusion"] = "Could not read the durable mission checkpoint."
        report["checks"]["authenticated_scope"] = {
            "passed": "operator" in session_scopes and "local-client" in session_scopes,
            "scopes": session_scopes,
        }
        return (0 if report["overall"] == "PASS" else 2), report
    except Exception as exc:
        report["overall"] = "BLOCKED"
        report["blocker"] = f"{type(exc).__name__}: {exc}"
        return 2, report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8181")
    parser.add_argument("--goal", default="Lista os repositórios locais",
                        help="Mission goal; must match a supported read-only auto-run intent.")
    parser.add_argument("--description", default="Diagnóstico read-only; não alterar ficheiros.",
                        help="Bounded mission context; no credentials or private session data.")
    parser.add_argument("--poll-timeout", type=int, default=90)
    parser.add_argument("--poll-interval", type=float, default=2.0)
    parser.add_argument("--request-timeout", type=float, default=5.0)
    parser.add_argument("--report-dir", type=Path, default=default_report_dir())
    args = parser.parse_args()
    if not 5 <= args.poll_timeout <= 300:
        parser.error("--poll-timeout must be between 5 and 300 seconds")
    if not 0.5 <= args.poll_interval <= 10:
        parser.error("--poll-interval must be between 0.5 and 10 seconds")
    if not 1 <= args.request_timeout <= 30:
        parser.error("--request-timeout must be between 1 and 30 seconds")

    exit_code, report = run(args)
    report["finished_at"] = utc_now()
    args.report_dir.mkdir(parents=True, exist_ok=True)
    filename = "live-mission-" + datetime.now().strftime("%Y%m%d-%H%M%S") + ".json"
    report_path = args.report_dir / filename
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Overall: {report['overall']}")
    print(f"Report: {report_path}")
    if report.get("mission"):
        state = mission_checkpoint_status(report["mission"])
        print(f"Mission: {report['mission'].get('mission_id')} / {state}")
    if report.get("blocker"):
        print(f"Blocker: {report['blocker']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
