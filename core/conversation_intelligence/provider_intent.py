"""Deterministic parser for explicit natural-language requests to consult AI providers.

This module only detects operator intent. It does not enqueue, approve, send, or
claim that a provider was contacted. Callers must keep the normal approval and
visible-browser transport controls in place.
"""
from __future__ import annotations

from dataclasses import dataclass
import re


PROVIDER_ORDER = ("chatgpt", "grok", "gemini", "claude", "deepseek", "qwen")

_PROVIDER_ALIASES = {
    "chatgpt": ("chatgpt", "chat gpt", "gpt"),
    "grok": ("grok",),
    "gemini": ("gemini",),
    "claude": ("claude",),
    "deepseek": ("deepseek", "deep seek"),
    "qwen": ("qwen",),
}

_PROVIDER_PATTERN = re.compile(
    r"(?<![\w])(" + "|".join(
        re.escape(alias)
        for aliases in _PROVIDER_ALIASES.values()
        for alias in sorted(aliases, key=len, reverse=True)
    ) + r")(?![\w])",
    re.IGNORECASE,
)

# Require an imperative/request verb. Merely mentioning an AI in a discussion
# must never silently dispatch a consultation.
_INTENT_PATTERN = re.compile(
    r"\b(?:"
    r"pede(?:-me)?\s+ajuda(?:\s+a)?|"
    r"pedir\s+ajuda(?:\s+a)?|"
    r"consulta(?:r)?|"
    r"questiona(?:r)?|"
    r"pergunta(?:r)?|"
    r"ask(?:\s+for)?\s+help\s+from|"
    r"get\s+(?:a\s+)?(?:second\s+)?opinion\s+from|"
    r"consult|"
    r"ask"
    r")\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class ProviderIntent:
    """A detected, explicit provider consultation request."""

    requested: bool
    providers: tuple[str, ...] = ()
    question: str = ""
    reason: str = "no_explicit_consultation_intent"


def _canonical_provider(value: str) -> str | None:
    normalized = re.sub(r"\s+", " ", value.casefold()).strip()
    for provider, aliases in _PROVIDER_ALIASES.items():
        if normalized in aliases:
            return provider
    return None


def parse_provider_intent(message: str) -> ProviderIntent:
    """Parse an explicit consultation command without causing side effects.

    Provider names are accepted only when an explicit consultation verb occurs
    before them. The returned provider list follows the stable product order,
    not the order in which aliases happen to be matched.
    """
    if not isinstance(message, str) or not message.strip():
        return ProviderIntent(False)

    intent = _INTENT_PATTERN.search(message)
    if intent is None:
        return ProviderIntent(False)
    # Explicit negation is not authorization to contact an external provider.
    prefix = message[max(0, intent.start() - 24):intent.start()]
    if re.search(r"\b(?:não|nao|never|don't|do not)\s*$", prefix, re.IGNORECASE):
        return ProviderIntent(False, reason="negated_consultation_intent")

    # Limit the provider search to the command clause. A later unrelated
    # provider mention should not expand the dispatch set.
    command_tail = message[intent.end():]
    clause_end = re.search(r"[\n.!?;]", command_tail)
    end = intent.end() + clause_end.start() if clause_end else len(message)
    # Only names following the explicit command verb authorize dispatch.
    clause = message[intent.end():end]
    matches = list(_PROVIDER_PATTERN.finditer(clause))
    providers = {
        provider
        for match in matches
        if (provider := _canonical_provider(match.group(1))) is not None
    }
    if not providers:
        return ProviderIntent(False, reason="explicit_intent_without_supported_provider")

    question = message[intent.end() + matches[-1].end():].strip()
    # If the user wrote a colon after the provider list, it belongs to the
    # command separator rather than to the question.
    question = re.sub(r"^[\s,:—–-]+", "", question).strip()
    if not question:
        # The complete user message remains useful as the consultation goal.
        question = message.strip()

    return ProviderIntent(
        requested=True,
        providers=tuple(provider for provider in PROVIDER_ORDER if provider in providers),
        question=question,
        reason="explicit_provider_consultation",
    )
