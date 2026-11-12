"""Launch an allowlisted AI provider home page in the operator's default browser.

This module deliberately does not inspect browser profiles, read credentials, send
messages, or claim that a provider page finished loading. The return value records
only the operating-system browser launch request.
"""
from __future__ import annotations

import webbrowser
from datetime import datetime, timezone
from typing import Any


PROVIDER_URLS = {
    "chatgpt": "https://chatgpt.com/",
    "gemini": "https://gemini.google.com/",
    "grok": "https://grok.com/",
    "claude": "https://claude.ai/",
    "deepseek": "https://chat.deepseek.com/",
    "qwen": "https://chat.qwen.ai/",
}


def launch_provider_home(provider: str) -> dict[str, Any]:
    """Request a visible default-browser launch for one fixed provider URL."""
    if not isinstance(provider, str) or provider not in PROVIDER_URLS:
        raise ValueError("Provider is not in the fixed browser-launch allowlist.")
    url = PROVIDER_URLS[provider]
    launched = bool(webbrowser.open(url, new=2, autoraise=True))
    if not launched:
        raise RuntimeError("The operating system did not accept the browser launch request.")
    return {
        "status": "OPEN_REQUESTED",
        "provider": provider,
        "url": url,
        "launch_accepted_by_os": True,
        "page_load_verified": False,
        "message_sent": False,
        "credentials_accessed": False,
        "launched_at": datetime.now(timezone.utc).isoformat(),
        "next_step": "The operator must confirm the provider page is open and pair the DGM-MAT browser extension if consultation is required.",
    }
