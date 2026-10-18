"""Deterministic, conservative routing for the small set of real mission handlers.

This router does not use an LLM and never authorizes mutating work. Unknown goals
remain unsupported until a real executor is registered for them.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class IntentDecision:
    intent: str
    supported: bool
    confidence: float
    requires_approval: bool
    reason: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


_READ_VERBS = {
    "list", "lists", "show", "shows", "display", "find", "which", "what",
    "listar", "lista", "listar", "mostra", "mostrar", "ver", "consultar",
    "quais", "enumera", "enumerar", "descobrir",
}
_REPOSITORY_WORDS = {
    "repo", "repos", "repository", "repositories",
    "repositorio", "repositorios",
}
_MUTATION_WORDS = {
    "create", "make", "write", "edit", "change", "modify", "update", "delete",
    "remove", "install", "run", "execute", "fix", "repair", "implement",
    "deploy", "commit", "push", "merge", "criar", "cria", "escrever",
    "editar", "alterar", "modificar", "atualizar", "apagar", "remover",
    "instalar", "executar", "corrigir", "reparar", "implementar", "publicar",
}


def _normalized_words(goal: str) -> list[str]:
    normalized = unicodedata.normalize("NFKD", goal.casefold())
    normalized = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    return re.findall(r"[a-z0-9]+", normalized)


def classify_mission_intent(goal: str) -> IntentDecision:
    """Classify only actions backed by a real, allowlisted implementation."""
    if not isinstance(goal, str) or len(goal.strip()) < 3:
        return IntentDecision("invalid", False, 1.0, True, "The mission goal is empty or too short.")

    words = _normalized_words(goal)
    word_set = set(words)

    # A read-only keyword must never override a mutating request in the same sentence.
    if word_set & _MUTATION_WORDS:
        return IntentDecision(
            "unsupported", False, 0.0, True,
            "The request contains a potentially mutating verb and has no registered executor.",
        )

    has_repository = bool(word_set & _REPOSITORY_WORDS)
    has_read_verb = bool(word_set & _READ_VERBS)
    if has_repository and has_read_verb:
        return IntentDecision(
            "list_repositories", True, 0.98, False,
            "Matched a read-only repository listing handler.",
        )

    return IntentDecision(
        "unsupported", False, 0.0, True,
        "No registered executor matches this mission. The request must not be treated as completed.",
    )
