"""Compatibility shim; implementation lives in DGM-MAT-Connectors."""

from .boundary import create_runtime_connectors

_connector = create_runtime_connectors()
ObsidianConnector = _connector["obsidian_class"]
obsidian_connector = _connector["obsidian"]
