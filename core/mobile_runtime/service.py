# Path: C:\ProgramasGodMode\DGM-MAT\core\mobile_runtime\service.py
from __future__ import annotations

import json
import os
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

    def create_thread(self, title: str = "Nova conversa", **kwargs: Any) -> dict[str, Any]:
        return self.store.create_thread(title, **kwargs).to_dict()

    def list_threads(self) -> list[dict[str, Any]]:
        return [thread.to_dict() for thread in self.store.list_threads()]

    def get_thread(self, thread_id: str) -> dict[str, Any] | None:
        thread = self.store.get_thread(thread_id)
        return thread.to_dict() if thread else None

    def rename(self, thread_id: str, title: str) -> dict[str, Any]:
        return self.store.rename(thread_id, title).to_dict()

    def append_user_message(self, thread_id: str, content: str) -> dict[str, Any]:
        thread = self.store.get_thread(thread_id)
        if thread is None:
            raise KeyError(thread_id)

        result = self.intent.interpret(content)
        mission_decision = classify_mission_intent(content)
        self.store.append_message(
            thread_id,
            "user",
            content,
            metadata={
                "intent": result.to_dict(),
                "mission_decision": mission_decision.to_dict(),
            },
        )

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
        if mission_decision.supported:
            mission = mission_engine.create_mission(
                goal=content,
                description=mission_decision.reason,
            )
            mission_id = mission.mission_id
            mission_requires_approval = bool(mission_decision.requires_approval)
            mission_status = getattr(mission.status, "value", mission.status)
            action_id = getattr(mission, "metadata", {}).get("action_id")
            action_queue = getattr(mission_engine, "action_queue", None)
            get_action = getattr(action_queue, "get_action", None)
            if isinstance(action_id, int) and callable(get_action):
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
                    "A aprovação explícita foi registada e a missão foi encaminhada para execução."
                    if mission_requires_approval
                    else "O handler read-only foi aprovado automaticamente pela allowlist e encaminhado para execução."
                )
                response_text = (
                    f"Missão {mission_id} registada ({mission_decision.intent}). "
                    + approval_source
                    + " O resultado ainda não foi confirmado."
                )
            elif action_status == "RUNNING":
                response_text = (
                    f"Missão {mission_id} registada ({mission_decision.intent}) e em execução "
                    "no trabalhador governado. Ainda não declaro conclusão."
                )
            elif action_status == "COMPLETED":
                response_text = (
                    f"A ação da missão {mission_id} terminou na fila governada. "
                    "Consulta o resultado persistido antes de considerar o trabalho validado."
                )
            elif action_status == "FAILED":
                response_text = (
                    f"A missão {mission_id} falhou no trabalhador governado. "
                    "O erro e o estado foram preservados para diagnóstico; não houve repetição automática."
                )
            elif mission_requires_approval or action_status == "QUEUED":
                response_text = (
                    f"Missão {mission_id} registada ({mission_decision.intent}) e pendente de aprovação. "
                    "Não foi executada qualquer ação."
                )
            else:
                response_text = (
                    f"Missão {mission_id} registada ({mission_decision.intent}); "
                    f"estado atual: {mission_status or 'desconhecido'}. "
                    "Não afirmo conclusão sem resultado persistido."
                )
        elif result.execution_candidate or result.intent in {"status", "research", "memory"}:
            response_text = self._unsupported_mission_response(result, mission_decision)
        else:
            response_text = self._generate_response(thread_id, result)

        assistant_metadata = {
            "intent": result.to_dict(),
            "mission_decision": mission_decision.to_dict(),
            "mission_id": mission_id,
            "mission_status": mission_status,
            "action_status": action_status,
            "mission_requires_approval": mission_requires_approval,
            "source": "dgm-mat-mobile-runtime",
        }
        self.store.append_message(
            thread_id,
            "assistant",
            response_text,
            metadata=assistant_metadata,
        )
        updated = self.store.get_thread(thread_id)
        return {
            "thread": updated.to_dict() if updated else None,
            "intent": result.to_dict(),
            "mission_decision": mission_decision.to_dict(),
            "mission_id": mission_id,
            "mission_status": mission_status,
            "action_status": action_status,
            "mission_requires_approval": mission_requires_approval,
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
