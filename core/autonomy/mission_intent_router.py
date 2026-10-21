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
_SUMMARY_WORDS = {
    "summary", "summarize", "summarise", "summarized", "summarised",
    "resumo", "resumir", "resume", "sintese", "sintetizar", "overview",
}
_ARCHITECTURE_TARGET_WORDS = {
    "architecture", "arquitetura", "structure", "estrutura",
    "project", "projeto", "repository", "repo", "system", "sistema",
    "departments", "departamentos",
}
_REPOSITORY_STATUS_TARGET_WORDS = {
    "git", "repo", "repository", "repositorio", "workspace", "project", "projeto",
}
_STATUS_WORDS = {"status", "estado", "situacao", "branch"}
_LOCAL_RESEARCH_VERBS = {
    "research", "search", "investigate", "look", "find", "explore",
    "pesquisa", "pesquisar", "procura", "procurar", "investiga",
    "investigar", "encontra", "encontrar", "explora", "explorar",
    "consulta", "consultar",
}
_LOCAL_RESEARCH_TARGET_WORDS = {
    "local", "repository", "repo", "repositorio", "code", "codebase",
    "codigo", "docs", "documentation", "documentacao", "workspace", "dgm",
}
_EXTERNAL_RESEARCH_WORDS = {"web", "internet", "online", "external", "externo", "externa"}
_MUTATION_WORDS = {
    "create", "creates", "make", "write", "writes", "edit", "edits", "change", "changes",
    "modify", "modifies", "update", "updates", "delete", "deletes", "remove", "removes",
    "install", "installs", "run", "runs", "execute", "executes", "fix", "fixes",
    "repair", "repairs", "implement", "implements", "deploy", "deploys", "commit", "commits",
    "push", "pushes", "merge", "merges", "criar", "cria", "crie", "escrever", "escreve",
    "editar", "edita", "edite", "alterar", "altera", "altere", "modificar", "modifica",
    "modifique", "atualizar", "atualiza", "atualize", "apagar", "apaga", "apague",
    "remover", "remove", "remova", "instalar", "instala", "instale", "executar",
    "executa", "execute", "corrigir", "corrige", "corrija", "reparar", "repara",
    "repare", "implementar", "implementa", "implemente", "publicar", "publica", "publique",
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
    has_summary = bool(word_set & _SUMMARY_WORDS) or {"visao", "geral"}.issubset(word_set)
    has_architecture_target = bool(word_set & _ARCHITECTURE_TARGET_WORDS)
    # Host diagnostics map only to fixed, read-only command IDs in CommandExecutor.
    # A mission can never supply arbitrary command text through this router.
    if "ollama" in word_set and bool(word_set & {
        "status", "estado", "model", "models", "modelo", "modelos",
        "version", "versao", "list", "lista", "listar", "ver", "mostrar", "mostra",
    }):
        return IntentDecision(
            "ollama_status", True, 0.98, False,
            "Matched the fixed read-only Ollama status/model inventory command.",
        )
    if "claude" in word_set and bool(word_set & {
        "status", "estado", "version", "versao", "instalado", "instalacao",
        "available", "availability", "disponivel",
    }):
        return IntentDecision(
            "claude_status", True, 0.97, False,
            "Matched the fixed read-only Claude Code availability/version command.",
        )
    if bool(word_set & {"engine", "engines", "motor", "motores"}) and bool(word_set & {
        "active", "ativos", "ativo", "running", "processos", "inventory", "inventario",
        "quais", "what", "which", "que",
    }):
        return IntentDecision(
            "engines_inventory", True, 0.94, False,
            "Matched the bounded process-name/PID inventory for known AI engines.",
        )

    if (
        bool(word_set & {"system", "host", "windows", "pc", "computador", "sistema"})
        and bool(word_set & (_SUMMARY_WORDS | _STATUS_WORDS | {"informacao", "informacoes", "info"}))
        and not bool(word_set & {"architecture", "arquitetura", "structure", "estrutura", "departments", "departamentos"})
    ):
        return IntentDecision(
            "system_summary", True, 0.94, False,
            "Matched the fixed read-only host/system summary command.",
        )
    if has_summary and has_architecture_target:
        return IntentDecision(
            "architecture_summary", True, 0.96, False,
            "Matched a read-only architecture summary backed by fixed local source documents.",
        )
    if bool(word_set & _STATUS_WORDS) and bool(word_set & _REPOSITORY_STATUS_TARGET_WORDS):
        return IntentDecision(
            "repository_status", True, 0.97, False,
            "Matched a fixed, read-only git status command scoped to the DGM-MAT repository root.",
        )
    if (
        bool(word_set & _LOCAL_RESEARCH_VERBS)
        and bool(word_set & _LOCAL_RESEARCH_TARGET_WORDS)
        and not bool(word_set & _EXTERNAL_RESEARCH_WORDS)
    ):
        return IntentDecision(
            "local_research", True, 0.94, False,
            "Matched bounded local-only code/documentation research with source locations.",
        )
    if has_repository and has_read_verb:
        return IntentDecision(
            "list_repositories", True, 0.98, False,
            "Matched a read-only repository listing handler.",
        )

    return IntentDecision(
        "unsupported", False, 0.0, True,
        "No registered executor matches this mission. The request must not be treated as completed.",
    )
