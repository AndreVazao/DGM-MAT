"""Local source discovery for reusable skills and modules.

This scanner only inventories candidates. It never imports or executes lab code.
Promotion happens through the SkillForge pipeline.
"""

from __future__ import annotations

import json
from pathlib import Path

from .capability_models import CapabilitySource


class LocalSourceDiscovery:
    MANIFEST_NAMES = (
        "SKILL.md",
        "README.md",
        "skill.json",
        "plugin.json",
        "package.json",
        "pyproject.toml",
        "manifest.json",
    )

    def __init__(self, roots: list[str | Path]) -> None:
        self.roots = [Path(root) for root in roots]

    def scan(self) -> list[CapabilitySource]:
        results: list[CapabilitySource] = []
        for root in self.roots:
            if not root.exists():
                continue
            for child in sorted(root.iterdir()):
                if not child.is_dir():
                    continue
                manifests = [p for p in self.MANIFEST_NAMES if (child / p).is_file()]
                nested_skills = list(child.rglob("SKILL.md"))[:20]
                if not manifests and not nested_skills:
                    continue
                capabilities = self._infer_capabilities(child)
                results.append(
                    CapabilitySource(
                        source_id=f"local:{child.name}",
                        name=child.name,
                        source_type="local_project",
                        locator=str(child),
                        capabilities=capabilities,
                        metadata={"manifests": ",".join(manifests)},
                    )
                )
        return results

    def _infer_capabilities(self, root: Path) -> list[str]:
        text_parts: list[str] = []
        for name in self.MANIFEST_NAMES:
            path = root / name
            if path.is_file():
                try:
                    text_parts.append(path.read_text(encoding="utf-8", errors="ignore")[:12000])
                except OSError:
                    pass
        text = "\n".join(text_parts).lower()
        capabilities: list[str] = []
        vocabulary = {
            "browser": ("browser", "playwright", "browser-act"),
            "voice": ("voice", "elevenlabs", "tts", "speech"),
            "openai": ("openai", "codex"),
            "anthropic": ("anthropic", "claude"),
            "gemini": ("gemini", "google ai"),
            "vercel": ("vercel",),
            "cloudflare": ("cloudflare",),
            "mobile": ("android", "mobile"),
            "mcp": ("mcp",),
            "automation": ("automation", "workflow"),
        }
        for capability, terms in vocabulary.items():
            if any(term in text for term in terms):
                capabilities.append(capability)
        return capabilities
