from dataclasses import dataclass

from core.contracts.mcp import (
    tool_definition_to_descriptor,
    tool_definitions_to_descriptors,
)


@dataclass
class FakeToolDefinition:
    name: str
    description: str
    inputSchema: dict


def test_mcp_tool_definition_maps_to_public_descriptor_without_importing_mcp():
    tool = FakeToolDefinition(
        name="filesystem",
        description="Read/write files",
        inputSchema={
            "type": "object",
            "required": ["action", "path"],
        },
    )

    descriptor = tool_definition_to_descriptor(tool)

    assert descriptor.name == "filesystem"
    assert descriptor.description == "Read/write files"
    assert descriptor.input_schema["required"] == ["action", "path"]
    assert descriptor.risk_class == "HIGH"
    assert descriptor.approval_policy == "REQUIRED"
    assert descriptor.allowed_transports == ["mcp"]
    assert "filesystem.write" in descriptor.capabilities


def test_unknown_tool_gets_conservative_default_policy():
    descriptor = tool_definition_to_descriptor(
        {
            "name": "future_tool",
            "description": "Future",
            "inputSchema": {"type": "object"},
        }
    )

    assert descriptor.risk_class == "HIGH"
    assert descriptor.approval_policy == "REQUIRED"
    assert descriptor.capabilities == ["tool.future_tool"]


def test_batch_conversion_preserves_order():
    descriptors = tool_definitions_to_descriptors(
        [
            {"name": "git", "description": "Git", "inputSchema": {}},
            {"name": "shell", "description": "Shell", "inputSchema": {}},
        ]
    )

    assert [item.name for item in descriptors] == ["git", "shell"]
    assert descriptors[0].risk_class == "MEDIUM"
    assert descriptors[1].risk_class == "CRITICAL"
