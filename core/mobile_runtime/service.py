# Path: C:\ProgramasGodMode\DGM-MAT\core\mobile_runtime\service.py
from __future__ import annotations

import asyncio
import json
import os
import re
import threading
import unicodedata
from uuid import uuid4
import subprocess
import urllib.error
import urllib.request
from typing import Any

from .intent import IntentInterpreter
from .models import IntentResult
from .store import ConversationStore
from core.autonomy.mission_engine import mission_engine
from core.autonomy.mission_intent_router import classify_mission_intent


class MobileConversationService:
    """Conversation surface: durable thread + intent + lightweight local AI response."""

    def __init__(self, store: ConversationStore | None = None) -> None:
        self.store = store or ConversationStore()
        self.intent = IntentInterpreter()
        self.auto_help_worker = None
        self._provider_rate_control = None
        self._provider_rate_lock = threading.Lock()

    def create_thread(self, title: str = "Nova conversa", **kwargs: Any) -> dict[str, Any]:
        return self.store.create_thread(title, **kwargs).to_dict()

    def list_threads(self) -> list[dict[str, Any]]:
        return [thread.to_dict() for thread in self.store.list_threads()]

    def get_thread(self, thread_id: str) -> dict[str, Any] | None:
        self._refresh_mission_updates(thread_id)
        thread = self.store.get_thread(thread_id)
        return thread.to_dict() if thread else None

    def _refresh_mission_updates(self, thread_id: str) -> None:
        """Append one durable conversation update when a linked mission changes state."""
        thread = self.store.get_thread(thread_id)
        if thread is None:
            return

        tracked: dict[str, tuple[str | None, str | None]] = {}
        for message in reversed(thread.messages):
            metadata = message.metadata if isinstance(message.metadata, dict) else {}
            mission_id = metadata.get("mission_update_for") or metadata.get("mission_id")
            if isinstance(mission_id, str) and mission_id and mission_id not in tracked:
                tracked[mission_id] = (
                    metadata.get("mission_status"),
                    metadata.get("action_status"),
                )

        for mission_id, previous in tracked.items():
            if not re.fullmatch(r"mission_[0-9a-f]{8}", mission_id):
                continue
            try:
                mission = mission_engine._reload_mission_checkpoint(mission_id)
                if mission is None:
                    continue
                status_value = getattr(mission.status, "value", mission.status)
                mission_status = str(status_value) if status_value is not None else None
                action_status = None
                action_id = mission.metadata.get("action_id") if isinstance(mission.metadata, dict) else None
                queue = getattr(mission_engine, "action_queue", None)
                get_action = getattr(queue, "get_action", None)
                if isinstance(action_id, int) and not isinstance(action_id, bool) and callable(get_action):
                    action = get_action(action_id)
                    if isinstance(action, dict):
                        raw_action_status = action.get("status")
                        action_status = str(getattr(raw_action_status, "value", raw_action_status)) if raw_action_status is not None else None
                current = (mission_status, action_status)
                if current == previous or not mission_status:
                    continue
                response = self._mission_status_update(mission_id, mission, mission_status, action_status)
                if not response:
                    continue
                self.store.append_message(
                    thread_id,
                    "assistant",
                    response,
                    metadata={
                        "mission_update_for": mission_id,
                        "mission_status": mission_status,
                        "action_status": action_status,
                        "source": "dgm-mat-mission-checkpoint",
                    },
                )
            except Exception:
                # Conversation reads must remain available if a mission checkpoint is damaged.
                continue

    @staticmethod
    def _mission_status_update(
        mission_id: str,
        mission: Any,
        mission_status: str,
        action_status: str | None,
    ) -> str | None:
        """Describe only the durable state observed; never infer successful execution."""
        if mission_status == "COMPLETED":
            metadata = mission.metadata if isinstance(mission.metadata, dict) else {}
            result = metadata.get("result") if isinstance(metadata.get("result"), dict) else {}
            summary = result.get("summary")
            output = result.get("output") or metadata.get("output")
            detail = summary.strip() if isinstance(summary, str) and summary.strip() else ""
            if not detail and isinstance(output, str) and output.strip():
                detail = output.strip()[:1200]
            suffix = f" Resultado registado: {detail}" if detail else " O checkpoint terminal est\u00e1 guardado; consulta o resultado persistido para os detalhes."
            return f"A miss\u00e3o {mission_id} foi conclu\u00edda segundo o checkpoint persistido.{suffix}"
        if mission_status == "FAILED":
            error = getattr(mission, "error", None)
            if not error and isinstance(getattr(mission, "metadata", None), dict):
                result = mission.metadata.get("result")
                if isinstance(result, dict):
                    error = result.get("summary") or result.get("error")
            detail = f" Motivo registado: {str(error)[:700]}" if error else ""
            return f"A miss\u00e3o {mission_id} terminou com falha. N\u00e3o foi repetida automaticamente.{detail}"
        if mission_status == "CANCELLED":
            return f"A miss\u00e3o {mission_id} foi cancelada. N\u00e3o foi retomada automaticamente."
        if mission_status == "RUNNING":
            return f"A miss\u00e3o {mission_id} est\u00e1 em execu\u00e7\u00e3o. Ainda n\u00e3o existe resultado final confirmado."
        if mission_status in {"QUEUED", "APPROVAL_PENDING"}:
            if action_status == "APPROVED":
                return f"A aprova\u00e7\u00e3o da miss\u00e3o {mission_id} foi registada. Aguarda o trabalhador governado; ainda n\u00e3o declaro execu\u00e7\u00e3o."
            return f"A miss\u00e3o {mission_id} continua pendente ({action_status or mission_status}). N\u00e3o foi declarada como executada."
        return None

    @staticmethod
    def _is_continuation_message(content: str) -> bool:
        if not isinstance(content, str):
            return False
        normalized = unicodedata.normalize("NFKD", content.casefold())
        normalized = "".join(char for char in normalized if not unicodedata.combining(char))
        normalized = re.sub(r"[^a-z0-9]+", " ", normalized).strip()
        return bool(re.fullmatch(
            r"(?:(?:ok|certo|entao|perfeito|boa)\s+)?"
            r"(?:(?:irmao|amigao)\s+)?"
            r"(?:avanca|continua|prossegue|segue|procede|vai em frente|segue em frente|"
            r"faz isso|go ahead|continue|proceed)"
            r"(?:\s+(?:irmao|amigao|com forca total|full force|o trabalho|em frente|ai))?",
            normalized,
        ))

    def _resolve_followup_context(self, thread: Any, content: str) -> dict[str, Any] | None:
        """Resolve short continuation commands without duplicating an active mission."""
        if not self._is_continuation_message(content):
            return None

        messages = list(getattr(thread, "messages", []))
        for index in range(len(messages) - 1, -1, -1):
            previous = messages[index]
            if getattr(previous, "role", None) != "user":
                continue
            metadata = previous.metadata if isinstance(previous.metadata, dict) else {}
            intent_data = metadata.get("intent") if isinstance(metadata.get("intent"), dict) else {}
            decision_data = metadata.get("mission_decision") if isinstance(metadata.get("mission_decision"), dict) else {}
            intent_name = intent_data.get("intent")
            actionable = (
                intent_data.get("execution_candidate") is True
                or intent_name in {"audit", "repair", "implement", "sync", "deploy", "research"}
                or decision_data.get("supported") is True
            )
            if not actionable:
                continue

            linked_reply = None
            for reply in messages[index + 1:]:
                if getattr(reply, "role", None) == "assistant":
                    reply_metadata = reply.metadata if isinstance(reply.metadata, dict) else {}
                    if (
                        reply_metadata.get("mission_id")
                        or reply_metadata.get("mission_update_for")
                        or reply_metadata.get("auto_help_request_id")
                    ):
                        linked_reply = dict(reply_metadata)
                        if linked_reply.get("mission_update_for"):
                            linked_reply["mission_id"] = linked_reply["mission_update_for"]
            linked_reply = linked_reply or {}
            mission_id = linked_reply.get("mission_id")
            if isinstance(mission_id, str) and re.fullmatch(r"mission_[0-9a-f]{8}", mission_id):
                mission_status = linked_reply.get("mission_status")
                action_status = linked_reply.get("action_status")
                if mission_status in {"CREATED", "QUEUED", "APPROVAL_PENDING", "RUNNING"} or action_status in {"QUEUED", "APPROVED", "RUNNING"}:
                    return {
                        "mode": "active",
                        "goal": previous.content,
                        "source_message_id": previous.id,
                        "mission_id": mission_id,
                        "mission_status": mission_status,
                        "action_status": action_status,
                        "mission_requires_approval": bool(linked_reply.get("mission_requires_approval")),
                    }
                return {
                    "mode": "clarify",
                    "goal": previous.content,
                    "source_message_id": previous.id,
                    "mission_id": mission_id,
                    "message": (
                        f"A miss\u00e3o anterior {mission_id} j\u00e1 terminou "
                        f"({mission_status or 'estado desconhecido'}). "
                        "Qual \u00e9 o pr\u00f3ximo objetivo que queres que eu execute?"
                    ),
                }

            return {
                "mode": "reuse",
                "goal": previous.content,
                "source_message_id": previous.id,
            }

        return {
            "mode": "clarify",
            "goal": content,
            "source_message_id": None,
            "message": (
                "Queres que eu continue, mas n\u00e3o encontrei uma miss\u00e3o anterior "
                "associada a esta conversa. Qual \u00e9 o projeto ou objetivo que devo retomar?"
            ),
        }

    def rename(self, thread_id: str, title: str) -> dict[str, Any]:
        return self.store.rename(thread_id, title).to_dict()

    def append_user_message(self, thread_id: str, content: str) -> dict[str, Any]:
        if not isinstance(content, str) or not content.strip():
            raise ValueError("A non-empty user message is required.")
        self._refresh_mission_updates(thread_id)
        thread = self.store.get_thread(thread_id)
        if thread is None:
            raise KeyError(thread_id)

        followup = self._resolve_followup_context(thread, content)
        followup_mode = followup.get("mode") if followup else None
        effective_goal = (
            followup.get("goal")
            if followup and followup_mode in {"reuse", "active", "clarify"}
            else content
        )
        if not isinstance(effective_goal, str) or not effective_goal.strip():
            effective_goal = content
        result = self.intent.interpret(effective_goal)
        mission_decision = classify_mission_intent(effective_goal)
        followup_metadata = {
            "mode": followup_mode,
            "source_message_id": followup.get("source_message_id") if followup else None,
            "related_mission_id": followup.get("mission_id") if followup else None,
        } if followup else None
        user_metadata = {
            "intent": result.to_dict(),
            "mission_decision": mission_decision.to_dict(),
        }
        if followup_metadata:
            user_metadata["followup"] = followup_metadata
            if effective_goal != content:
                user_metadata["resolved_goal"] = effective_goal
        self.store.append_message(thread_id, "user", content, metadata=user_metadata)

        if thread.title == "Nova conversa":
            auto_title = self._suggest_title(content, result)
            self.store.rename(thread_id, auto_title)

        if result.project_hint or result.repository_hint:
            self.store.update_context(
                thread_id,
                project=result.project_hint,
                repository=result.repository_hint,
            )

        mission_id = None
        mission_status = None
        action_status = None
        mission_requires_approval = False
        auto_help_request_id = None

        if followup_mode == "active":
            mission_id = followup.get("mission_id")
            mission_status = followup.get("mission_status")
            action_status = followup.get("action_status")
            mission_requires_approval = bool(followup.get("mission_requires_approval"))
            status_label = action_status or mission_status or "estado desconhecido"
            response_text = (
                f"Entendi a continua\u00e7\u00e3o. J\u00e1 existe a miss\u00e3o {mission_id} "
                f"({status_label}); n\u00e3o criei uma miss\u00e3o duplicada. "
                "Acompanho o mesmo trabalho e atualizo esta conversa quando o checkpoint mudar."
            )
        elif followup_mode == "clarify":
            response_text = followup["message"]
        else:
            if mission_decision.supported:
                mission = mission_engine.create_mission(
                    goal=effective_goal,
                    description=mission_decision.reason,
                )
                mission_id = mission.mission_id
                mission_requires_approval = bool(mission_decision.requires_approval)
                mission_status = getattr(mission.status, "value", mission.status)
                action_id = getattr(mission, "metadata", {}).get("action_id")
                action_queue = getattr(mission_engine, "action_queue", None)
                get_action = getattr(action_queue, "get_action", None)
                if isinstance(action_id, int) and not isinstance(action_id, bool) and callable(get_action):
                    action = get_action(action_id)
                    if isinstance(action, dict):
                        raw_status = action.get("status")
                        action_status = getattr(raw_status, "value", raw_status)
                current_mission = getattr(mission_engine, "active_missions", {}).get(mission_id)
                if current_mission is not None:
                    mission_status = getattr(current_mission.status, "value", current_mission.status)

            if mission_id:
                if action_status == "APPROVED":
                    approval_source = (
                        "A aprova\u00e7\u00e3o expl\u00edcita foi registada e a miss\u00e3o foi encaminhada para execu\u00e7\u00e3o."
                        if mission_requires_approval
                        else "O handler read-only foi aprovado automaticamente pela allowlist e encaminhado para execu\u00e7\u00e3o."
                    )
                    response_text = (
                        f"Miss\u00e3o {mission_id} registada ({mission_decision.intent}). "
                        + approval_source
                        + " O resultado ainda n\u00e3o foi confirmado."
                    )
                elif action_status == "RUNNING":
                    response_text = (
                        f"Miss\u00e3o {mission_id} registada ({mission_decision.intent}) e em execu\u00e7\u00e3o "
                        "no trabalhador governado. Ainda n\u00e3o declaro conclus\u00e3o."
                    )
                elif action_status == "COMPLETED":
                    response_text = (
                        f"A a\u00e7\u00e3o da miss\u00e3o {mission_id} terminou na fila governada. "
                        "Consulta o resultado persistido antes de considerar o trabalho validado."
                    )
                elif action_status == "FAILED":
                    response_text = (
                        f"A miss\u00e3o {mission_id} falhou no trabalhador governado. "
                        "O erro e o estado foram preservados para diagn\u00f3stico; n\u00e3o houve repeti\u00e7\u00e3o autom\u00e1tica."
                    )
                elif mission_requires_approval or action_status == "QUEUED":
                    response_text = (
                        f"Miss\u00e3o {mission_id} registada ({mission_decision.intent}) e pendente de aprova\u00e7\u00e3o. "
                        "N\u00e3o foi executada qualquer a\u00e7\u00e3o."
                    )
                else:
                    response_text = (
                        f"Miss\u00e3o {mission_id} registada ({mission_decision.intent}); "
                        f"estado atual: {mission_status or 'desconhecido'}. "
                        "N\u00e3o afirmo conclus\u00e3o sem resultado persistido."
                    )
            elif result.execution_candidate or result.intent in {"status", "research", "memory"}:
                response_text = self._unsupported_mission_response(result, mission_decision)
                if followup_mode == "reuse":
                    response_text = (
                        "Percebi que a tua continuação se refere ao pedido anterior. "
                        + response_text
                    )
            else:
                response_text = self._generate_response(thread_id, result)

        # Unsupported actionable requests remain non-executable, but can ask the
        # allowlisted free Hub providers for a consultative plan in the background.
        if (
            followup_mode not in {"active", "clarify"}
            and mission_id is None
            and not mission_decision.supported
            and result.intent in {"repair", "implement", "deploy", "sync", "audit", "research"}
            and self.auto_help_worker is not None
        ):
            try:
                help_request = self.auto_help_worker.enqueue(
                    thread_id=thread_id,
                    goal=effective_goal,
                    reason=mission_decision.reason,
                )
                auto_help_request_id = help_request.get("request_id")
                help_status = help_request.get("status")
                if help_request.get("duplicate"):
                    if help_request.get("cached_response"):
                        response_text += (
                            "\n\nJ\u00e1 existe uma consulta recente para este pedido. "
                            "Reutilizei o resultado guardado e n\u00e3o voltei a chamar os fornecedores."
                        )
                    else:
                        response_text += (
                            f"\n\nJ\u00e1 existe uma consulta {auto_help_request_id} "
                            f"com estado {help_status}; n\u00e3o criei outra nem repeti o pedido."
                        )
                elif help_status == "PENDING":
                    response_text += (
                        f"\n\nRegistei a consulta gratuita {auto_help_request_id}. "
                        "O DGM-MAT vai pedir uma segunda opini\u00e3o ao Kilo/LLM7 em segundo plano. "
                        "As respostas ser\u00e3o guardadas nesta thread como sugest\u00f5es n\u00e3o verificadas; "
                        "n\u00e3o autorizam execu\u00e7\u00e3o nem altera\u00e7\u00f5es."
                    )
                elif help_status == "BLOCKED_SECRET_CONTENT":
                    response_text += (
                        "\n\nA consulta externa foi bloqueada porque o pedido parece conter "
                        "credenciais ou segredos. N\u00e3o foi enviado a nenhum fornecedor."
                    )
                elif help_status == "DISABLED":
                    response_text += (
                        "\n\nA ajuda externa autom\u00e1tica est\u00e1 desligada; o pedido ficou guardado "
                        "e n\u00e3o foi enviado a fornecedores."
                    )
                elif help_status == "BLOCKED_NO_FREE_PROVIDER":
                    response_text += (
                        "\n\nN\u00e3o h\u00e1 fornecedor gratuito autorizado configurado. "
                        "N\u00e3o foi feita qualquer chamada externa."
                    )
            except Exception as exc:
                response_text += (
                    f"\n\nN\u00e3o consegui registar a consulta externa ({type(exc).__name__}); "
                    "n\u00e3o foi feita qualquer chamada nem repeti\u00e7\u00e3o autom\u00e1tica."
                )

        assistant_metadata = {
            "intent": result.to_dict(),
            "mission_decision": mission_decision.to_dict(),
            "mission_id": mission_id,
            "mission_status": mission_status,
            "action_status": action_status,
            "mission_requires_approval": mission_requires_approval,
            "auto_help_request_id": auto_help_request_id,
            "source": "dgm-mat-mobile-runtime",
        }
        if followup_metadata:
            assistant_metadata["followup"] = followup_metadata
            if effective_goal != content:
                assistant_metadata["resolved_goal"] = effective_goal
        self.store.append_message(thread_id, "assistant", response_text, metadata=assistant_metadata)
        updated = self.store.get_thread(thread_id)
        return {
            "thread": updated.to_dict() if updated else None,
            "intent": result.to_dict(),
            "mission_decision": mission_decision.to_dict(),
            "mission_id": mission_id,
            "mission_status": mission_status,
            "action_status": action_status,
            "mission_requires_approval": mission_requires_approval,
            "auto_help_request_id": auto_help_request_id,
            "resolved_goal": effective_goal if followup_mode == "reuse" else None,
            "followup_mode": followup_mode,
            "message": response_text,
        }

    def _unsupported_mission_response(self, intent: IntentResult, decision: Any) -> str:
        if intent.intent == "status":
            return (
                "Pedido de estado guardado na thread, mas não corresponde a um diagnóstico "
                "registado. Experimenta: 'estado do PC', 'estado do repositório DGM-MAT' "
                "ou 'estado do Ollama'. Não foi executado nenhum comando."
            )
        if intent.intent == "memory":
            return (
                "A mensagem ficou guardada nesta conversa, mas não foi promovida à memória "
                "persistente. Essa operação ainda não tem um handler de memória ligado ao runtime."
            )
        if intent.intent == "research":
            return (
                "A pesquisa foi registada na thread, mas não encontrei um handler local compatível "
                "com o âmbito pedido. Não foi feita pesquisa externa nem executado qualquer comando."
            )
        return (
            f"Pedido reconhecido como '{intent.intent}', mas o DGM-MAT não tem um executor "
            f"registado para esta operação ({decision.reason}). Não foi criada missão nem "
            "executada qualquer alteração. Os handlers read-only suportados continuam disponíveis."
        )

    def _suggest_title(self, content: str, intent: IntentResult) -> str:
        cleaned = " ".join(content.strip().split())
        if len(cleaned) <= 48:
            return cleaned
        return cleaned[:45].rstrip() + "..."

    def _generate_response(self, thread_id: str, intent: IntentResult) -> str:
        thread = self.store.get_thread(thread_id)
        if thread is None:
            return "A thread deixou de existir."

        if intent.intent == "chat":
            governed_response = self._try_governed_provider_chat(thread, intent)
            if governed_response:
                return governed_response

        llm_response = self._try_local_llm(thread, intent)
        if llm_response:
            return llm_response

        if intent.intent == "status":
            return "Percebi. Vou tratar isto como pedido de estado real do DGM-MAT e manter esta conversa como a thread de trabalho."
        if intent.intent == "sync":
            return "Percebi. O objetivo é sincronizar PC, telemóvel, GitHub, memória e rendezvous sem transformar a Vercel no plano de execução."
        if intent.intent == "implement":
            return "Percebi o objetivo e mantenho-o nesta thread. A implementação fica como candidata de execução; ações destrutivas ou irreversíveis continuam a exigir aprovação."
        if intent.intent == "audit":
            return "Percebi. Vou tratar isto como uma auditoria baseada na realidade do código, documentação e estado dos repositórios."
        if intent.intent == "repair":
            return "Percebi. Vou tratar isto como reparação controlada, preservando contexto, provas e checkpoints."
        if intent.intent == "research":
            return "Percebi. Vou tratar isto como investigação e manter as conclusões ligadas à thread."
        if intent.intent == "memory":
            return "Percebi. Isto deve ficar associado à memória persistente, não apenas à conversa."
        if intent.intent == "deploy":
            return "Percebi o pedido de publicação. Antes de um release efetivo, o cockpit deve mostrar a ação e pedir aprovação quando necessário."
        return "Percebi. Mantive a mensagem e o contexto nesta conversa para que o próximo pedido continue exatamente daqui."

    def governed_chat_status(self) -> dict[str, Any]:
        """Report opt-in governed-chat readiness without sending a provider request."""
        enabled = os.getenv("DGM_MOBILE_GOVERNED_CHAT_ENABLED", "0").strip().casefold() in {"1", "true", "yes", "on"}
        provider_id = os.getenv("DGM_MOBILE_GOVERNED_PROVIDER", "nvidia_nim").strip() or "nvidia_nim"
        result = {
            "enabled": enabled,
            "provider_id": provider_id,
            "registered": False,
            "available": False,
            "policy": "explicit opt-in; verified free-tier providers only; no tools, shell or paid fallback",
        }
        if not enabled:
            result["reason"] = "disabled_by_configuration"
            return result
        try:
            from core.provider_sync.provider_registry import initialize_default_providers, provider_registry
            initialize_default_providers()
            provider = provider_registry.get_provider(provider_id)
            result["registered"] = provider is not None
            result["available"] = bool(provider and provider.is_available())
            if provider is None:
                result["reason"] = "provider_not_registered"
            elif not result["available"]:
                result["reason"] = "provider_not_healthy_or_quota_unavailable"
            else:
                result["reason"] = "ready"
        except Exception as exc:
            result["reason"] = f"readiness_check_failed:{type(exc).__name__}"
        return result

    def _try_governed_provider_chat(self, thread: Any, intent: IntentResult) -> str | None:
        """Use only an explicitly enabled, policy-governed free provider for ordinary chat."""
        if os.getenv("DGM_MOBILE_GOVERNED_CHAT_ENABLED", "0").strip().casefold() not in {"1", "true", "yes", "on"}:
            return None
        provider_id = os.getenv("DGM_MOBILE_GOVERNED_PROVIDER", "nvidia_nim").strip() or "nvidia_nim"
        try:
            from core.mobile_runtime.auto_help import _contains_secret
            from core.governance.provider_rate_control import ProviderRateControl
            from core.provider_sync.governed_provider_service import GovernedProviderService
            from core.provider_sync.provider_request_policy import ProviderRequestPolicy
            from core.provider_sync.provider_registry import initialize_default_providers, provider_registry

            history = thread.messages[-8:]
            normalized: list[dict[str, str]] = []
            system_prompt = (
                "?s o assistente conversacional do DGM-MAT. Responde sempre em Portugu?s de Portugal. "
                "Mant?m continuidade com o hist?rico e usa o projeto/reposit?rio indicados. "
                "N?o afirmes que executaste, alteraste, testaste ou publicaste algo sem confirma??o expl?cita "
                "do runtime. N?o executes ferramentas: este canal ? apenas conversa. "
                "Se o pedido exigir uma a??o, explica que ser? encaminhado pelo fluxo de miss?es governado; "
                "n?o inventes permiss?es, estado, resultados ou capacidades. "
                f"Projeto: {thread.project or 'n?o indicado'}. "
                f"Reposit?rio: {thread.repository or 'n?o indicado'}. "
                f"Inten??o determin?stica observada: {intent.intent}."
            )
            if _contains_secret(system_prompt):
                return None
            normalized.append({"role": "system", "content": system_prompt})
            total_chars = len(system_prompt)
            for item in history:
                role = getattr(item, "role", None)
                content = getattr(item, "content", None)
                if role not in {"user", "assistant"} or not isinstance(content, str) or not content.strip():
                    continue
                content = content.strip()
                if _contains_secret(content):
                    return None
                content = content[-1400:]
                if total_chars + len(content) > 7600:
                    continue
                normalized.append({"role": role, "content": content})
                total_chars += len(content)
            if len(normalized) < 2:
                return None

            initialize_default_providers()
            provider = provider_registry.get_provider(provider_id)
            if provider is None:
                return None
            if (
                getattr(provider, "requires_governed_request_id", False) is True
                and provider.is_available() is not True
            ):
                health_check = getattr(provider, "check_health", None)
                if not callable(health_check):
                    return None
                observation = health_check()
                if not isinstance(observation, dict) or observation.get("available") is not True:
                    return None
            with self._provider_rate_lock:
                if self._provider_rate_control is None:
                    self._provider_rate_control = ProviderRateControl(max_requests=10)
                rate_control = self._provider_rate_control
            service = GovernedProviderService(
                ProviderRequestPolicy(provider_registry, rate_control),
                timeout_seconds=35.0,
            )
            request_id = f"mobile-{thread.id}-{uuid4().hex[:16]}"
            execution = asyncio.run(service.execute_chat(
                provider_id=provider_id,
                request_id=request_id,
                messages=normalized,
            ))
            if execution.success and isinstance(execution.response, str) and execution.response.strip():
                return execution.response.strip()
            return None
        except Exception:
            return None

    def _try_local_llm(self, thread: Any, intent: IntentResult) -> str | None:
        # Fail safe: local inference may use an already-running Ollama instance,
        # but must not start a background process unless explicitly opted in.
        mode = os.getenv("DGM_MOBILE_LOCAL_LLM", "manual").strip().lower()
        if mode not in {"off", "manual", "auto"}:
            mode = "manual"
        if mode == "off":
            return None

        # The current PC has only ~3 GB RAM. Do not start/load Ollama when the
        # operating system cannot safely provide at least 1.2 GB to the model.
        try:
            import psutil
            if psutil.virtual_memory().available < 1_200_000_000:
                return None
        except ImportError:
            return None

        model = os.getenv("DGM_OLLAMA_MODEL", "")
        if not model:
            model = self._select_installed_model(intent)
        if not model:
            return None

        try:
            if not self._ollama_available():
                if mode != "auto":
                    return None
                self._start_ollama()
            if not self._ollama_available():
                return None

            history = thread.messages[-10:]
            transcript = "\n".join(
                f"{message.role.upper()}: {message.content}" for message in history
            )
            prompt = (
                "You are the lightweight local assistant inside DGM-MAT. "
                "Reply in European Portuguese. Preserve the user's intent. "
                "Do not claim an action was executed unless the runtime explicitly says so. "
                "Be concise on this low-memory PC.\n\n"
                f"Detected intent: {intent.intent}\n"
                f"Project: {thread.project or 'unknown'}\n"
                f"Repository: {thread.repository or 'unknown'}\n"
                f"Conversation:\n{transcript}\n\n"
                "Assistant:"
            )
            request = urllib.request.Request(
                "http://127.0.0.1:11434/api/generate",
                data=json.dumps({
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"num_ctx": 4096, "temperature": 0.2},
                }).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(request, timeout=45) as response:
                payload = json.loads(response.read().decode("utf-8"))
            answer = str(payload.get("response") or "").strip()
            return answer or None
        except (OSError, ValueError, urllib.error.URLError, subprocess.SubprocessError):
            return None

    def _ollama_available(self) -> bool:
        try:
            with urllib.request.urlopen("http://127.0.0.1:11434/api/version", timeout=2):
                return True
        except OSError:
            return False

    def _start_ollama(self) -> None:
        executable = os.path.expandvars(
            r"%LOCALAPPDATA%\Programs\Ollama\ollama.exe"
        )
        if not os.path.exists(executable):
            return
        try:
            subprocess.Popen(
                [executable, "serve"],
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except OSError:
            return

    def _select_installed_model(self, intent: IntentResult) -> str | None:
        preferred = (
            ["qwen2.5-coder:1.5b", "deepseek-r1:1.5b", "qwen2.5:1.5b"]
            if intent.intent in {"implement", "repair", "audit"}
            else ["llama3.2:1b", "qwen2.5:1.5b", "gemma2:2b"]
        )
        try:
            with urllib.request.urlopen("http://127.0.0.1:11434/api/tags", timeout=2) as response:
                names = {item.get("name") for item in json.loads(response.read().decode("utf-8")).get("models", [])}
            for model in preferred:
                if model in names:
                    return model
        except (OSError, ValueError):
            return None
        return None
