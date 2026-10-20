"""Test-only stand-in for the optional external DGM-MAT-Connectors package.

Only used by API/security unit tests when the real satellite package is not installed.
It deliberately reports the Obsidian integration as unavailable and performs no I/O.
"""


class ObsidianConnector:
    def index_vault(self):
        return {"status": "unavailable", "reason": "test-only connector stub"}


obsidian_connector = ObsidianConnector()
