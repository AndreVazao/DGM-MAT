# Path: C:\ProgramasGodMode\DGM-MAT\core\api\security_policy.py
"""Explicit API security inventory and reusable fail-closed auth primitives.

The inventory is enforced by LocalSessionAuthMiddleware in api_server.py.
Route classification is still not proof of security by itself; keep remote binding
prohibited until all client migration and negative enforcement tests pass.
"""
from __future__ import annotations
import hmac
from dataclasses import dataclass
from enum import Enum
from typing import Iterable

class SecurityScope(str, Enum):
    PUBLIC_HEALTH = "public-health"
    LOCAL_CLIENT = "local-client"
    OPERATOR = "operator"
    PROVIDER_API = "provider-api"
    PROVIDER_OPERATOR = "provider-operator"
    LOCAL_DOCUMENTATION = "local-documentation"
    LOCAL_STATIC_CLIENT = "local-static-client"

@dataclass(frozen=True)
class RouteClassification:
    methods: tuple[str, ...]
    path: str
    scope: SecurityScope
    note: str

# Explicit inventory: update this table when registering routes.
ROUTE_CLASSIFICATIONS: tuple[RouteClassification, ...] = (
    RouteClassification(("GET", "HEAD"), "/openapi.json", SecurityScope.LOCAL_DOCUMENTATION, "OpenAPI schema; local development only."),
    RouteClassification(("GET", "HEAD"), "/docs", SecurityScope.LOCAL_DOCUMENTATION, "Interactive API docs; local development only."),
    RouteClassification(("GET", "HEAD"), "/docs/oauth2-redirect", SecurityScope.LOCAL_DOCUMENTATION, "Swagger OAuth redirect helper."),
    RouteClassification(("GET", "HEAD"), "/redoc", SecurityScope.LOCAL_DOCUMENTATION, "ReDoc; local development only."),
    RouteClassification(("WS",), "/ws", SecurityScope.LOCAL_CLIENT, "Realtime stream; currently unauthenticated."),
    RouteClassification(("WS",), "/runtime/ws", SecurityScope.LOCAL_CLIENT, "Compatibility realtime stream; currently unauthenticated."),
    RouteClassification(("GET",), "/health", SecurityScope.PUBLIC_HEALTH, "Minimal process health check."),
    RouteClassification(("POST",), "/auth/session", SecurityScope.OPERATOR, "Loopback-only bootstrap exchange; issues short-lived local session."),
    RouteClassification(("GET",), "/auth/pairing-code", SecurityScope.OPERATOR, "Issues one-time mobile pairing code to loopback PC clients only."),
    RouteClassification(("POST",), "/auth/pair", SecurityScope.OPERATOR, "Exchanges one-time pairing code for a short-lived operator session."),
    RouteClassification(("GET",), "/runtime/health", SecurityScope.LOCAL_CLIENT, "Runtime health."),
    RouteClassification(("GET",), "/runtime/status", SecurityScope.LOCAL_CLIENT, "Runtime status and telemetry."),
    RouteClassification(("GET",), "/runtime/state", SecurityScope.LOCAL_CLIENT, "Runtime state snapshot."),
    RouteClassification(("GET",), "/runtime/truth", SecurityScope.LOCAL_CLIENT, "Runtime truth snapshot."),
    RouteClassification(("GET",), "/runtime/reality", SecurityScope.LOCAL_CLIENT, "Reality/provider observations."),
    RouteClassification(("GET",), "/runtime/degradation", SecurityScope.LOCAL_CLIENT, "Degradation details."),
    RouteClassification(("GET",), "/runtime/repo_scan", SecurityScope.OPERATOR, "Filesystem/repository scan."),
    RouteClassification(("GET",), "/runtime/memory/stats", SecurityScope.LOCAL_CLIENT, "Memory statistics."),
    RouteClassification(("GET",), "/runtime/memory", SecurityScope.LOCAL_CLIENT, "Memory subsystem status."),
    RouteClassification(("GET",), "/runtime/providers", SecurityScope.LOCAL_CLIENT, "Provider status."),
    RouteClassification(("GET",), "/runtime/governance", SecurityScope.LOCAL_CLIENT, "Governance status."),
    RouteClassification(("GET",), "/runtime/autonomy", SecurityScope.LOCAL_CLIENT, "Autonomy/task status."),
    RouteClassification(("GET",), "/runtime/workspace/scan", SecurityScope.OPERATOR, "Workspace scan."),
    RouteClassification(("GET",), "/runtime/obsidian/index", SecurityScope.OPERATOR, "Indexes local vault."),
    RouteClassification(("POST",), "/runtime/missions", SecurityScope.OPERATOR, "Creates a mission."),
    RouteClassification(("GET",), "/runtime/missions", SecurityScope.LOCAL_CLIENT, "Mission details/logs."),
    RouteClassification(("GET",), "/runtime/missions/{mission_id}", SecurityScope.LOCAL_CLIENT, "One durable mission checkpoint and result; read-only."),
    RouteClassification(("GET",), "/runtime/office/telemetry", SecurityScope.LOCAL_CLIENT, "Content-minimized read-only mission/queue telemetry for the virtual office."),
    RouteClassification(("POST",), "/runtime/approvals/{request_id}", SecurityScope.OPERATOR, "Mission approval decision."),
    RouteClassification(("GET",), "/runtime/approvals", SecurityScope.OPERATOR, "Pending approvals."),
    RouteClassification(("GET",), "/runtime/queue", SecurityScope.OPERATOR, "Action queue details."),
    RouteClassification(("POST",), "/runtime/queue/actions/{action_id}/approve", SecurityScope.OPERATOR, "Explicit operator approval of one durable queue action."),
    RouteClassification(("POST",), "/runtime/queue/actions/{action_id}/reject", SecurityScope.OPERATOR, "Explicit operator rejection of one durable queue action."),
    RouteClassification(("GET",), "/mobile/status", SecurityScope.LOCAL_CLIENT, "Mobile service status."),
    RouteClassification(("GET",), "/mobile/usb-recovery/diagnose", SecurityScope.OPERATOR, "Read-only USB/ADB device diagnostics."),
    RouteClassification(("GET",), "/mobile/usb-recovery/state", SecurityScope.OPERATOR, "Automatic USB/ADB recovery monitor state."),
    RouteClassification(("POST",), "/mobile/usb-recovery/repair", SecurityScope.OPERATOR, "Allowlisted USB/ADB recovery; APK reinstall requires explicit confirmation."),
    RouteClassification(("GET",), "/mobile/threads", SecurityScope.LOCAL_CLIENT, "Conversation list."),
    RouteClassification(("POST",), "/mobile/threads", SecurityScope.OPERATOR, "Creates a conversation."),
    RouteClassification(("GET",), "/mobile/threads/{thread_id}", SecurityScope.LOCAL_CLIENT, "Conversation content/history."),
    RouteClassification(("POST",), "/mobile/threads/{thread_id}/messages", SecurityScope.OPERATOR, "Writes a message; may trigger work."),
    RouteClassification(("POST",), "/mobile/threads/{thread_id}/rename", SecurityScope.OPERATOR, "Renames a conversation."),
    RouteClassification(("GET",), "/mobile/capabilities", SecurityScope.LOCAL_CLIENT, "Capability inventory."),
    RouteClassification(("POST",), "/mobile/capability-scout", SecurityScope.OPERATOR, "Capability discovery action."),
    RouteClassification(("GET",), "/governance/audit/workspace", SecurityScope.OPERATOR, "Workspace audit."),
    RouteClassification(("GET",), "/governance/audit/self", SecurityScope.OPERATOR, "Self audit."),
    RouteClassification(("GET",), "/governance/repair/self/plan", SecurityScope.OPERATOR, "Self-repair plan."),
    RouteClassification(("POST",), "/governance/repair/self/apply", SecurityScope.OPERATOR, "Potentially mutating repair."),
    RouteClassification(("POST",), "/governance/conversations/analyze", SecurityScope.OPERATOR, "Processes submitted conversation content."),
    RouteClassification(("GET",), "/governance/runtime-capabilities", SecurityScope.OPERATOR, "Read-only observed host capability snapshot."),
    RouteClassification(("GET",), "/governance/commands/catalog", SecurityScope.OPERATOR, "Lists allowlisted read-only local diagnostics."),
    RouteClassification(("POST",), "/governance/commands/run", SecurityScope.OPERATOR, "Runs one allowlisted read-only local diagnostic."),
    RouteClassification(("POST",), "/provider-execution/requests", SecurityScope.PROVIDER_API, "Provider request intake."),
    RouteClassification(("GET",), "/provider-execution/approvals", SecurityScope.PROVIDER_OPERATOR, "Provider approvals."),
    RouteClassification(("POST",), "/provider-execution/approvals/{approval_task_id}/decision", SecurityScope.PROVIDER_OPERATOR, "Provider approval decision."),
    RouteClassification(("POST",), "/provider-execution/execute", SecurityScope.PROVIDER_API, "Executes stored approved provider envelope."),
    RouteClassification(("MOUNT",), "/app", SecurityScope.LOCAL_STATIC_CLIENT, "Optional mobile static client."),
)

def classify_route(path: str, methods: Iterable[str] | None = None, route_type: str = "http") -> RouteClassification | None:
    """Return exact route classification, or None if not inventoried."""
    normalized = tuple(sorted({str(method).upper() for method in (methods or ())}))
    if route_type.casefold() == "websocket":
        normalized = ("WS",)
    elif route_type.casefold() == "mount":
        normalized = ("MOUNT",)
    for entry in ROUTE_CLASSIFICATIONS:
        if entry.path == path and entry.methods == normalized:
            return entry
    return None

def classify_request_path(path: str, method: str, route_type: str = "http") -> RouteClassification | None:
    """Classify a concrete request path against the explicit route inventory.

    This fallback handles framework route wrappers that do not expose their
    canonical template consistently. It requires exact segment counts and
    treats a whole {parameter} segment as one non-empty path segment.
    """
    normalized_method = str(method).upper()
    if route_type.casefold() == "websocket":
        normalized_method = "WS"
    elif route_type.casefold() == "mount":
        normalized_method = "MOUNT"

    request_parts = path.strip("/").split("/")
    for entry in ROUTE_CLASSIFICATIONS:
        if entry.methods != (normalized_method,):
            continue
        template_parts = entry.path.strip("/").split("/")
        if len(template_parts) != len(request_parts):
            continue
        matched = all(
            (part.startswith("{") and part.endswith("}") and bool(actual))
            or part == actual
            for part, actual in zip(template_parts, request_parts)
        )
        if matched:
            return entry
    return None


def bearer_matches(authorization: str | None, expected_token: str | None) -> bool:
    """Strict constant-time bearer comparison; missing config fails closed."""
    if not isinstance(expected_token, str) or not expected_token or not isinstance(authorization, str):
        return False
    scheme, separator, supplied = authorization.partition(" ")
    if not separator or scheme.casefold() != "bearer" or not supplied:
        return False
    if supplied.strip() != supplied or " " in supplied or "\t" in supplied:
        return False
    return hmac.compare_digest(supplied.encode("utf-8"), expected_token.encode("utf-8"))
