"""Bounded natural-language search across locally imported AI conversation archives."""
from __future__ import annotations

import os
import re
import tempfile
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_STOP_WORDS = {
    "busca", "buscar", "pesquisa", "pesquisar", "procura", "procurar",
    "encontra", "encontrar", "recupera", "recuperar", "search", "find", "look",
    "conversa", "conversas", "conversation", "conversations", "chat", "chats",
    "historico", "historicos", "history", "do", "da", "de", "das", "dos", "o",
    "a", "os", "as", "um", "uma", "uns", "umas", "sobre", "acerca", "com",
    "para", "por", "no", "na", "nos", "nas", "the", "of", "for", "about",
    "in", "on", "and", "e", "ao", "aos", "projeto", "project", "projecto",
    "chatgpt", "gpt", "openai", "grok", "gemini", "claude", "deepseek", "qwen",
    "resumo", "resume", "resumir", "summary", "summarize", "organiza", "organizar",
    "mostra", "mostrar", "apresenta", "apresentar", "dossier", "dossie",
    "ia", "ias", "ai", "provider", "fornecedor",
}


def _fold(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value.casefold())
    return "".join(char for char in normalized if not unicodedata.combining(char))


def extract_search_terms(goal: str) -> list[str]:
    """Keep meaningful project/topic terms while dropping command and provider words."""
    tokens = re.findall(r"[A-Za-zÀ-ÿ0-9][A-Za-zÀ-ÿ0-9._-]*", goal)
    terms: list[str] = []
    seen: set[str] = set()
    for token in tokens:
        folded = _fold(token).strip("._-")
        if len(folded) < 2 or folded in _STOP_WORDS or folded in seen:
            continue
        seen.add(folded)
        terms.append(token.strip("._-"))
        if len(terms) >= 3:
            break
    return terms


def _provider_filter(goal: str) -> str | None:
    words = set(re.findall(r"[a-z0-9]+", _fold(goal)))
    for provider, aliases in (
        ("chatgpt", {"chatgpt", "openai"}),
        ("grok", {"grok"}),
        ("gemini", {"gemini"}),
        ("claude", {"claude"}),
        ("deepseek", {"deepseek"}),
        ("qwen", {"qwen"}),
    ):
        if words & aliases:
            return provider
    return None


def _search_archive_term(term: str, provider: str | None, limit: int) -> dict[str, Any]:
    # Lazy import keeps recovery API initialization out of ordinary chat startup.
    from core.api.recovery_api import search_recovery_sources
    return search_recovery_sources(q=term, provider=provider, limit=limit)


def _safe_slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", _fold(value)).strip("-")
    return slug[:64] or "conversation-search"


def _write_report(
    goal: str,
    terms: list[str],
    provider: str | None,
    results: list[dict[str, Any]],
    coverage: dict[str, Any],
) -> Path:
    root = Path(os.getenv(
        "DGM_CONVERSATION_SEARCH_REPORT_DIR",
        str(Path.home() / ".dgm-mat" / "reports" / "conversation-search"),
    )).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S-%f")
    report = root / f"{stamp}-{_safe_slug(' '.join(terms))}.md"
    lines = [
        "# DGM-MAT — Pesquisa de conversas",
        "",
        f"- Pedido: {goal.strip()}",
        f"- Gerado em UTC: {datetime.now(timezone.utc).isoformat()}",
        f"- Fornecedor: {provider or 'todos os fornecedores importados'}",
        f"- Termos pesquisados: {', '.join(terms)}",
        f"- Conversas encontradas: {len(results)}",
        f"- Fontes verificadas: {coverage.get('scanned_sources', 0)}",
        f"- Pesquisa truncada: {bool(coverage.get('truncated'))}",
        "- Cobertura: arquivos locais importados; não representa o histórico integral das contas.",
        "- Pesquisa de conteúdo integral nesta versão: ChatGPT importado; outros fornecedores podem devolver apenas metadados.",
        "- Acesso direto a contas de fornecedores: não utilizado.",
        "",
        "## Resultados",
        "",
    ]
    if not results:
        lines.append("_Não foram encontradas correspondências nos arquivos importados disponíveis._")
    for index, item in enumerate(results, 1):
        lines.extend([
            f"### {index}. {item.get('title') or 'Conversa sem título'}",
            "",
            f"- Fornecedor: {item.get('provider', 'desconhecido')}",
            f"- Data: {item.get('source_date') or 'não disponível'}",
            f"- ID: `{item.get('source_id', '')}`",
            f"- Correspondências: {', '.join(item.get('matched_terms', []))}",
            f"- Tipo: {item.get('match_type', 'metadata')}",
            f"- Estado da captura: {item.get('capture_status') or 'não registado'}",
            f"- URL original: {item.get('source_url') or 'não disponível'}",
            "",
            str(item.get("snippet") or "").replace("\r", " ").replace("\n", " ")[:420],
            "",
        ])
    lines.extend([
        "## Limites e confiança",
        "",
        "- O relatório contém excertos limitados, não transcrições completas.",
        "- A ausência de resultados não prova que a conversa não exista na conta original.",
        "- Conversas não importadas, apagadas, privadas ou fora do arquivo local não foram pesquisadas.",
        "- Os resultados são evidência de origem; propostas de IA não são decisões aprovadas.",
        "",
    ])
    content = "\n".join(lines)
    fd, temporary = tempfile.mkstemp(prefix=f".{report.name}.", suffix=".tmp", dir=str(root))
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, report)
    except Exception:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise
    return report


def search_archived_conversations(goal: str, *, limit: int = 15) -> dict[str, Any]:
    """Search a small number of terms in imported archives and write a local evidence report."""
    if not isinstance(goal, str) or len(goal.strip()) < 3:
        raise ValueError("A pesquisa precisa de uma instrução com pelo menos três caracteres.")
    if not 1 <= limit <= 25:
        raise ValueError("O limite de resultados deve estar entre 1 e 25.")
    terms = extract_search_terms(goal)
    if not terms:
        raise ValueError("Não consegui identificar o assunto da pesquisa na tua frase.")
    provider = _provider_filter(goal)

    merged: dict[tuple[str, str], dict[str, Any]] = {}
    scanned_sources = scanned_bytes = 0
    truncated = False
    for term in terms:
        payload = _search_archive_term(term, provider, limit)
        scanned_sources += int(payload.get("scanned_sources", 0) or 0)
        scanned_bytes += int(payload.get("scanned_bytes", 0) or 0)
        truncated = truncated or bool(payload.get("truncated"))
        for raw in payload.get("results", []):
            if not isinstance(raw, dict):
                continue
            key = (str(raw.get("provider") or ""), str(raw.get("source_id") or ""))
            if not key[0] or not key[1]:
                continue
            item = merged.setdefault(key, {**raw, "matched_terms": []})
            if term not in item["matched_terms"]:
                item["matched_terms"].append(term)
            if raw.get("match_type") == "message":
                item.update({key: value for key, value in raw.items() if value is not None})
    results = sorted(
        merged.values(),
        key=lambda item: (
            len(item.get("matched_terms", [])),
            str(item.get("source_date") or ""),
            str(item.get("title") or ""),
        ),
        reverse=True,
    )[:limit]
    coverage = {
        "scanned_sources": scanned_sources,
        "scanned_bytes": scanned_bytes,
        "truncated": truncated,
        "provider_access_used": False,
        "full_history_verified": False,
        "transcript_search_providers": ["chatgpt"],
    }
    report = _write_report(goal, terms, provider, results, coverage)
    summary = (
        f"Encontrei {len(results)} conversas nos arquivos locais importados."
        if results else
        "Não encontrei correspondências nos arquivos locais importados."
    )
    output_lines = [
        summary,
        f"Termos pesquisados: {', '.join(terms)}.",
        f"Fornecedor: {provider or 'todos os arquivos importados'}.",
        f"Relatório guardado em: {report}",
        "Cobertura: arquivo local importado; o histórico integral da conta não foi verificado.",
    ]
    for item in results[:8]:
        output_lines.append(
            f"- [{item.get('provider')}] {item.get('title') or item.get('source_id')}: "
            f"{str(item.get('snippet') or '')[:220]}"
        )
    return {
        "status": "completed",
        "summary": summary,
        "output": "\n".join(output_lines),
        "result_count": len(results),
        "results": results,
        "query_terms": terms,
        "provider_filter": provider,
        "dossier_path": str(report),
        "coverage": coverage,
        "provider_access_used": False,
        "full_history_verified": False,
        "transcript_search_providers": ["chatgpt"],
        "source_modified": False,
    }
