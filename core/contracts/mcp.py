"""One-way adapter from DGM-MCP tool metadata to DGM-Contracts.

This module deliberately does not import DGM-MCP.  DGM-MCP remains a transport
and tool-definition source; DGM-Contracts remains the public schema authority.
"""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from dgm_contracts import ToolDescriptor


_TOOL_POLICY: dict[str, tuple[str, str, list[str]]] = {
    "filesystem": ("HIGH", "REQUIRED", ["filesystem.read", "filesystem.write"]),
    "git": ("MEDIUM", "REQUIRED", ["git.status", "git.commit"]),
    "shell": ("CRITICAL", "REQUIRED", ["shell.execute"]),
    "patch": ("HIGH", "REQUIRED", ["patch.preview", "patch.write"]),
    "repo": ("HIGH", "REQUIRED", ["repo.init", "repo.clone"]),
}


def _read(tool: Any, key: str, default: Any = None) -> Any:
    if isinstance(tool, Mapping):
        return tool.get(key, default)
    return getattr(tool, key, default)


def tool_definition_to_descriptor(
    tool: Any,
    *,
    transport: str = "mcp",
    version: str = "1.0",
) -> ToolDescriptor:
    """Convert a DGM-MCP ToolDefinition-shaped object into ToolDescriptor.

    Accepts both the DGM-MCP dataclass and plain dictionaries so Core never
    depends on DGM-MCP's private Python classes.
    """
    name = str(_read(tool, "name", "")).strip()
    description = str(_read(tool, "description", "")).strip()
    input_schema = _read(tool, "inputSchema", None)
    if input_schema is None:
        input_schema = _read(tool, "input_schema", {})
    if not name:
        raise ValueError("Tool definition requires a non-empty name")
    if not isinstance(input_schema, Mapping):
        raise TypeError("Tool definition input schema must be a mapping")

    risk_class, approval_policy, capabilities = _TOOL_POLICY.get(
        name,
        ("HIGH", "REQUIRED", [f"tool.{name}"]),
    )
    return ToolDescriptor(
        name=name,
        description=description,
        input_schema=dict(input_schema),
        capabilities=capabilities,
        risk_class=risk_class,
        approval_policy=approval_policy,
        allowed_transports=[transport],
        version=version,
    )


def tool_definitions_to_descriptors(
    tools: list[Any] | tuple[Any, ...],
    *,
    transport: str = "mcp",
    version: str = "1.0",
) -> list[ToolDescriptor]:
    """Convert a deterministic collection of tool definitions."""
    return [
        tool_definition_to_descriptor(tool, transport=transport, version=version)
        for tool in tools
    ]
