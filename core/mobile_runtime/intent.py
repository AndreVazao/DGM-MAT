# Path: C:\ProgramasGodMode\DGM-MAT\core\mobile_runtime\intent.py
from __future__ import annotations

import re

from .models import IntentResult


class IntentInterpreter:
    """Cheap deterministic intent layer; no LLM is required to understand commands."""

    _patterns = [
        ("status", ("estado", "status", "como está", "como esta", "saúde", "saude", "verifica")),
        ("audit", ("audita", "auditar", "auditoria", "analisa", "analisar", "verifica o código", "verifica o codigo")),
        ("repair", ("corrige", "corrigir", "repara", "reparar", "resolve", "resolver", "conserta")),
        ("implement", ("avança", "avanca", "implementa", "implementar", "cria", "criar", "faz", "fazer", "desenvolve", "desenvolver")),
        ("sync", ("sincroniza", "sincronizar", "sync", "atualiza github", "atualiza a memória", "atualiza a memoria")),
        ("research", ("pesquisa", "pesquisar", "investiga", "investigar", "procura", "procurar")),
        ("memory", ("memória", "memoria", "recorda", "lembrar", "guarda isto", "guarda isso")),
        ("deploy", ("deploy", "publica", "publicar", "faz release", "release")),
    ]

    _repo_pattern = re.compile(r"(?:repo(?:sit[oó]rio)?|github)\s*[:=]?\s*([\w.-]+/[\w.-]+)", re.I)
    _project_pattern = re.compile(r"(?:projeto|projecto|project)\s*[:=]?\s*([^,.;]+)", re.I)

    def interpret(self, text: str) -> IntentResult:
        normalized = " ".join(text.lower().split())
        intent = "chat"
        confidence = 0.55
        evidence: list[str] = []

        for candidate, phrases in self._patterns:
            if any(phrase in normalized for phrase in phrases):
                intent = candidate
                confidence = 0.88
                evidence.append(f"keyword:{candidate}")
                break

        repo_match = self._repo_pattern.search(text)
        project_match = self._project_pattern.search(text)
        repository_hint = repo_match.group(1) if repo_match else None
        project_hint = project_match.group(1).strip() if project_match else None

        if repository_hint:
            evidence.append("explicit_repository")
        if project_hint:
            evidence.append("explicit_project")

        requires_approval = intent in {"deploy"} or any(
            phrase in normalized
            for phrase in (
                "apaga",
                "apagar",
                "elimina",
                "eliminar",
                "remove o repo",
                "remove o repositório",
                "remove o repositorio",
                "destrói",
                "destroi",
            )
        )

        execution_candidate = intent in {
            "audit",
            "repair",
            "implement",
            "sync",
            "deploy",
        }

        summary = text.strip()
        if intent == "chat":
            summary = "Conversa geral; preservar o contexto da thread."
        elif intent == "status":
            summary = "Consultar o estado real do DGM-MAT, PC, memória e conectividade."
        elif intent == "sync":
            summary = "Sincronizar o estado relevante entre PC, GitHub, memória e cockpit."
        elif intent == "implement":
            summary = "Transformar o pedido numa missão de implementação, sem executar ações destrutivas implicitamente."

        return IntentResult(
            intent=intent,
            summary=summary,
            confidence=confidence,
            project_hint=project_hint,
            repository_hint=repository_hint,
            action=intent,
            requires_approval=requires_approval,
            execution_candidate=execution_candidate,
            evidence=evidence,
        )
