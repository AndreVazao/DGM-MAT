"""Typed, fail-closed registry for the existing read-only command catalog.

This adapter exposes metadata and structured dispatch only. It does not add tools,
accept shell text, change mission routing, or bypass the durable approval queue.
"""
from __future__ import annotations

from typing import Any, Mapping

from dgm_contracts import ToolDescriptor

from core.operations.command_executor import CATALOG, CommandDenied, CommandExecutor, CommandSpec


class ReadOnlyToolRegistry:
    """Expose the fixed CommandExecutor catalog as typed local tool descriptors."""

    SCHEMA_VERSION = "dgm-mat.read-only-tool-registry.v1"
    TRANSPORT = "local"

    def __init__(self, executor: CommandExecutor | None = None) -> None:
        self._executor = executor or CommandExecutor()
        self._specs: dict[str, CommandSpec] = {
            spec.command_id: spec for spec in CATALOG
        }
        if len(self._specs) != len(CATALOG):
            raise RuntimeError("Read-only command catalog contains duplicate IDs.")

    @staticmethod
    def _input_schema(spec: CommandSpec) -> dict[str, Any]:
        properties: dict[str, Any] = {}
        required: list[str] = []
        if spec.requires_target:
            properties["target_path"] = {
                "type": "string",
                "minLength": 1,
                "description": "Existing Git working-tree path inside configured allowed roots.",
            }
            required.append("target_path")
        return {
            "type": "object",
            "properties": properties,
            "required": required,
            "additionalProperties": False,
        }

    def _descriptor(self, spec: CommandSpec) -> ToolDescriptor:
        return ToolDescriptor(
            name=spec.command_id,
            description=spec.description,
            input_schema=self._input_schema(spec),
            capabilities=["command.read", f"command.{spec.command_id}"],
            risk_class="LOW",
            # Metadata remains conservative. Existing runtime allowlists, not this
            # descriptor, decide whether a mission can run without operator approval.
            approval_policy="REQUIRED",
            allowed_transports=[self.TRANSPORT],
            version="1.0",
        )

    def list_tools(self) -> list[ToolDescriptor]:
        """Return fresh descriptors in the deterministic catalog order."""
        return [self._descriptor(spec) for spec in CATALOG]

    def get_tool(self, tool_id: str) -> ToolDescriptor:
        """Return one descriptor; unknown IDs are denied rather than synthesized."""
        if not isinstance(tool_id, str) or tool_id not in self._specs:
            raise CommandDenied("Tool is not registered in the read-only catalog.")
        return self._descriptor(self._specs[tool_id])

    def execute(self, tool_id: str, arguments: Mapping[str, Any] | None = None) -> dict[str, Any]:
        """Dispatch a registered command using validated structured arguments only."""
        if not isinstance(tool_id, str) or tool_id not in self._specs:
            raise CommandDenied("Tool is not registered in the read-only catalog.")
        if arguments is None:
            arguments = {}
        if not isinstance(arguments, Mapping):
            raise CommandDenied("Tool arguments must be an object.")

        spec = self._specs[tool_id]
        allowed_keys = {"target_path"} if spec.requires_target else set()
        supplied_keys = set(arguments.keys())
        if supplied_keys - allowed_keys:
            raise CommandDenied("Tool arguments contain unsupported fields.")
        if spec.requires_target:
            target_path = arguments.get("target_path")
            if not isinstance(target_path, str) or not target_path.strip():
                raise CommandDenied("This tool requires a non-empty target_path.")
        else:
            target_path = None

        # CommandExecutor retains final target-root validation, argv construction,
        # shell=False, fixed command bodies, timeout and output bounds.
        return self._executor.execute(tool_id, target_path=target_path)
