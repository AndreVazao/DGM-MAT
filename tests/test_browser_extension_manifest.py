from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXTENSION = ROOT / "browser_extension"


def test_extension_uses_manifest_v3_and_minimal_permissions():
    manifest = json.loads((EXTENSION / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["manifest_version"] == 3
    assert set(manifest["permissions"]) == {"activeTab", "storage"}
    denied = {"cookies", "history", "webRequest", "debugger", "downloads", "scripting", "management"}
    assert not denied.intersection(manifest["permissions"])
    assert all("://" in host for host in manifest["host_permissions"])
    assert all(
        host.startswith(("http://127.0.0.1:8181/", "http://localhost:8181/", "https://"))
        for host in manifest["host_permissions"]
    )


def test_extension_only_matches_chatgpt_gemini_and_grok_origins():
    manifest = json.loads((EXTENSION / "manifest.json").read_text(encoding="utf-8"))
    matches = manifest["content_scripts"][0]["matches"]
    assert any("chatgpt.com" in item for item in matches)
    assert any("chat.openai.com" in item for item in matches)
    assert any("gemini.google.com" in item for item in matches)
    assert any("bard.google.com" in item for item in matches)
    assert any("grok.com" in item for item in matches)
    assert any("x.com/i/grok" in item for item in matches)
    assert any("chat.deepseek.com" in item for item in matches)
    assert any("chat.qwen.ai" in item for item in matches)
    assert len(matches) == 8


def test_extension_never_reads_auth_stores_or_calls_provider_private_apis():
    content = (EXTENSION / "content.js").read_text(encoding="utf-8")
    background = (EXTENSION / "background.js").read_text(encoding="utf-8")
    forbidden = ("chrome.cookies", "localStorage", "sessionStorage", "indexedDB", "document.cookie")
    combined = content + "\n" + background
    for marker in forbidden:
        assert marker not in combined
    assert "DGM_DISCOVER_VISIBLE" in content
    assert "DGM_CAPTURE_CURRENT" in content
    assert "/recovery/browser-capture/discover" in background
    assert "/recovery/browser-capture/capture" in background


def test_extension_uses_only_the_local_dgm_mat_api_endpoint():
    background = (EXTENSION / "background.js").read_text(encoding="utf-8")
    assert 'const API = "http://127.0.0.1:8181";' in background
    assert "fetch(API + path" in background
