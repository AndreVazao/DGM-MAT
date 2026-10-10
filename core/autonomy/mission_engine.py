import json
import subprocess
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from uuid import uuid4
from datetime import datetime, timedelta

from core.autonomy.mission_models import Mission, MissionStatus, SubTask
from core.storage.storage_manager import storage_manager
from core.observability.logger import dgm_logger
from core.runtime.runtime_state_store import state_store, StateEvents
from core.runtime.safe_action_queue import SafeActionQueue, ActionStatus
from core.execution.approval_manager import ApprovalManager
from core.realtime.realtime_broadcast import safe_broadcast
from core.organization import CapabilityScout, InternalMessageBus, Message, MessagePriority
from core.organization.worker_runtime import WorkerRuntime
from core.organization.qa_intake_worker import QAIntakeWorker
from core.organization.qa_review_queue import QAReviewQueue
from core.organization.qa_review_coordinator import QAReviewCoordinator
from core.organization.help_seeking import HelpContext, HelpSeekingPolicy
from core.organization.specialist_collaboration import SpecialistCollaborationStore
from core.organization.validated_learning import ValidatedLessonStore
from core.providers.browser.governed_browser_session import GovernedBrowserSession

class MissionEngine:
    REPO_SCAN_ROOTS = [Path("C:/ProgramasGodMode"), Path("C:/DevopGodMode")]
    REPO_SCAN_LIMIT = 20
    BRANCH_SCAN_LIMIT = 20
    REPO_TIMEOUT_SECONDS = 5.0
    MISSION_EXECUTION_TIMEOUT_SECONDS = 60.0

    def __init__(self, organization_bus: InternalMessageBus | None = None):
        self.missions_path = storage_manager.get_path("missions")
        self.missions_path.mkdir(parents=True, exist_ok=True)
        self.active_missions: Dict[str, Mission] = {}
        self.approval_manager = ApprovalManager()
        self.capability_scout = CapabilityScout()
        self.organization_bus = organization_bus or InternalMessageBus(
            storage_manager.get_path("tasks") / "organization_messages.sqlite3"
        )
        self.worker_runtime = WorkerRuntime(self.organization_bus)
        self.qa_review_queue = QAReviewQueue(
            storage_manager.get_path("tasks") / "qa_review_queue.sqlite3"
        )
        self.qa_intake_worker = QAIntakeWorker(self.qa_review_queue)
        self.worker_runtime.register_handler(self.qa_intake_worker.agent_id, self.qa_intake_worker)
        # Existing review requests still target agent:bug-hunter; this handler only triages intake.
        self.worker_runtime.register_handler("agent:bug-hunter", self.qa_intake_worker)
        self.collaboration_store = SpecialistCollaborationStore(
            storage_manager.get_path("tasks") / "specialist_collaborations"
        )
        self.validated_lesson_store = ValidatedLessonStore(
            storage_manager.get_path("evolution_memory") / "validated_specialist_lessons"
        )
        self.qa_review_coordinator = QAReviewCoordinator(
            self.qa_review_queue, self.collaboration_store, self.validated_lesson_store,
            Path(__file__).resolve().parents[2],
        )
        # Browser sessions are ephemeral, in-memory only, and never exported to disk.
        self.browser_sessions: Dict[str, GovernedBrowserSession] = {}
        self.browser_screenshot_dir = storage_manager.get_path("tasks") / "browser_screenshots"
        self.action_queue = SafeActionQueue()
        self.action_queue.register_handler("MISSION_EXECUTION", self._handle_queue_execution)
        self.timeout_threshold = timedelta(seconds=self.MISSION_EXECUTION_TIMEOUT_SECONDS)
        self._load_missions()

    def register_organization_worker(self, agent_id: str, handler):
        """Register an explicit local handler; no implicit AI/provider is activated."""
        self.worker_runtime.register_handler(agent_id, handler)

    def dispatch_organization_message(self, agent_id: str):
        """Dispatch at most one durable unread message to a registered local worker."""
        return self.worker_runtime.dispatch_one(agent_id)

    def dispatch_pending_review_intake(self):
        """Triage one legacy Bug Hunter inbox request; this is not an independent review."""
        return self.worker_runtime.dispatch_one("agent:bug-hunter")

    def prepare_qa_review(self, work_item_id: str, *, reviewer_id: str):
        """Claim a persisted specialist result for independent local review."""
        return self.qa_review_coordinator.prepare(work_item_id, reviewer_id=reviewer_id)

    def run_qa_local_verification(self, work_item_id: str, *, reviewer_id: str):
        """Run the coordinator's fixed local checks; never executes result-provided commands."""
        return self.qa_review_coordinator.run_local_verification(work_item_id, reviewer_id=reviewer_id)

    def finalize_qa_review(self, work_item_id: str, **review):
        """Record an explicit independent PASS/FAIL decision and guarded lesson promotion."""
        return self.qa_review_coordinator.finalize(work_item_id, **review)

    def reconcile_qa_review_lesson(self, work_item_id: str, *, reviewer_id: str):
        """Recover lesson persistence after a collaboration was validated but storage failed."""
        return self.qa_review_coordinator.reconcile_validated_lesson(work_item_id, reviewer_id=reviewer_id)

    def start_governed_browser_session(
        self, *, allowed_hosts: list[str], headed: bool = True, timeout_ms: int = 15000
    ) -> Dict[str, Any]:
        """Open an ephemeral browser session limited to explicitly authorized HTTPS hosts."""
        if len(self.browser_sessions) >= 3:
            raise RuntimeError("At most three governed browser sessions may be active")
        session = GovernedBrowserSession(
            allowed_hosts=allowed_hosts,
            headed=headed,
            timeout_ms=timeout_ms,
            screenshot_dir=self.browser_screenshot_dir,
        )
        info = session.start()
        handle = f"browser_{uuid4().hex[:12]}"
        self.browser_sessions[handle] = session
        return {
            "handle": handle,
            "session_id": info.session_id,
            "current_url": info.current_url,
            "title": info.title,
            "headed": info.headed,
            "allowed_hosts": list(info.allowed_hosts),
            "cookies_persisted": False,
            "storage_state_exported": False,
        }

    def _get_governed_browser_session(self, handle: str) -> GovernedBrowserSession:
        session = self.browser_sessions.get(handle)
        if session is None:
            raise KeyError(f"Unknown or closed browser session: {handle}")
        return session

    def browser_navigate(self, handle: str, url: str) -> Dict[str, Any]:
        return self._get_governed_browser_session(handle).navigate(url)

    def browser_read_page(self, handle: str, *, max_chars: int = 20000) -> Dict[str, Any]:
        return self._get_governed_browser_session(handle).read_page(max_chars=max_chars)

    def browser_click(self, handle: str, selector: str) -> Dict[str, Any]:
        return self._get_governed_browser_session(handle).click(selector)

    def browser_fill(self, handle: str, selector: str, value: str) -> Dict[str, Any]:
        return self._get_governed_browser_session(handle).fill(selector, value)

    def browser_scroll(self, handle: str, *, direction: str = "down", pixels: int = 600) -> Dict[str, Any]:
        return self._get_governed_browser_session(handle).scroll(direction=direction, pixels=pixels)

    def browser_screenshot(self, handle: str, filename: str) -> Dict[str, Any]:
        return self._get_governed_browser_session(handle).screenshot(filename)

    def browser_ocr_screenshot(self, handle: str, filename: str, *, language: str = "por+eng") -> Dict[str, Any]:
        return self._get_governed_browser_session(handle).ocr_screenshot(filename, language=language)

    def close_governed_browser_session(self, handle: str) -> Dict[str, Any]:
        session = self.browser_sessions.pop(handle, None)
        if session is None:
            return {"closed": False, "reason": "unknown_or_already_closed"}
        session.close()
        return {"closed": True, "handle": handle, "cookies_persisted": False}

    def _load_missions(self):
        """Restores missions from storage."""
        for mission_file in self.missions_path.glob("*.json"):
            try:
                with open(mission_file, "r") as f:
                    data = json.load(f)
                    mission = Mission(
                        mission_id=data["mission_id"],
                        goal=data["goal"],
                        description=data.get("description", ""),
                        status=MissionStatus(data["status"]),
                        metadata=data.get("metadata", {}),
                        created_at=datetime.fromisoformat(data.get("created_at", datetime.now().isoformat())),
                        progress=data.get("progress", 0.0),
                        logs=data.get("logs", []),
                        error=data.get("error")
                    )
                    self.active_missions[mission.mission_id] = mission
                    self._sync_state(mission)
            except Exception as e:
                dgm_logger.error(f"MissionEngine: Failed to load mission {mission_file}: {e}")

    def create_mission(self, goal: str, description: str) -> Mission:
        mission_id = f"mission_{uuid4().hex[:8]}"

        # Validation Logic
        status = MissionStatus.CREATED
        metadata = {}
        error_msg = None

        if not goal or len(goal) < 3:
            status = MissionStatus.FAILED
            error_msg = "Goal too short or invalid"
            metadata["error"] = error_msg
            dgm_logger.warning(f"MissionEngine: Mission {mission_id} FAILED validation: {goal}")

        mission = Mission(
            mission_id=mission_id,
            goal=goal,
            description=description,
            status=status,
            metadata=metadata,
            error=error_msg
        )

        if status == MissionStatus.CREATED:
            mission.logs.append(f"Mission created with goal: {goal}")
            dgm_logger.info(f"MISSION_CREATED: {mission_id} - {goal}")
        else:
            mission.logs.append(f"Mission creation failed: {error_msg}")
            dgm_logger.error(f"MISSION_FAILED: {mission_id} - {goal}")

        self.active_missions[mission_id] = mission
        self.save_mission(mission)
        self._sync_state(mission)

        if status != MissionStatus.FAILED:
            # Enqueue in SafeActionQueue for visibility and execution control
            action_id = self.action_queue.enqueue("MISSION_EXECUTION", {
                "mission_id": mission_id,
                "goal": goal
            })
            mission.metadata["action_id"] = action_id
            dgm_logger.info(f"QUEUE_PUSHED: Action {action_id} for mission {mission_id}")

            # Transition to QUEUED immediately
            self._update_status(mission, MissionStatus.QUEUED)

            # For "lista as minhas repos", we auto-approve in the queue for demonstration/testing
            if "lista" in goal.lower() and "repos" in goal.lower():
                dgm_logger.info(f"MissionEngine: Auto-approving {mission_id} in queue.")
                self.action_queue.approve(action_id, operator="system_auto")

        return mission

    def _capability_request_from_goal(self, goal: str) -> Optional[str]:
        """Extract an explicit capability-gap signal without invoking execution."""
        normalized = goal.strip()
        lowered = normalized.lower()
        markers = (
            "não temos capacidade", "não tenho capacidade",
            "não temos essa capacidade", "não tenho essa capacidade",
            "não consigo", "não conseguimos",
            "capability missing", "missing capability", "need a capability",
            "preciso de uma capacidade", "precisamos de uma capacidade",
        )
        if not any(marker in lowered for marker in markers):
            return None

        separators = (" para ", " de ", " em ", ":", "-", "—")
        for separator in separators:
            if separator in normalized:
                candidate = normalized.split(separator, 1)[1].strip(" .,:;-—")
                if candidate:
                    return candidate[:200]
        return normalized[:200]

    def discover_capability_for_mission(
        self,
        mission: Mission,
        capability: str | None = None,
    ) -> Dict[str, Any]:
        """Ask the Capability Scout to find reusable sources for a mission gap.

        Discovery is deliberately read-only: no promotion, import or execution occurs.
        """
        requested_capability = (capability or self._capability_request_from_goal(mission.goal) or "").strip()
        if not requested_capability:
            return {"status": "not_requested", "mission_id": mission.mission_id}

        reason = mission.description or mission.goal
        report = self.capability_scout.discover(
            capability=requested_capability,
            reason=reason,
            mission_id=mission.mission_id,
        )
        mission.metadata["capability_discovery"] = report
        mission.logs.append(
            f"Capability Scout searched the approved ecosystem for: {requested_capability}"
        )
        self.organization_bus.send(
            Message(
                sender_id="agent:hq-orchestrator",
                recipient_id=CapabilityScout.agent_id,
                subject=f"Capability discovery completed: {requested_capability}",
                body=json.dumps(report, ensure_ascii=False),
                mission_id=mission.mission_id,
                priority=MessagePriority.NORMAL,
                requires_response=False,
            )
        )
        self.save_mission(mission)
        self._sync_state(mission)
        dgm_logger.info(
            f"CAPABILITY_DISCOVERY_COMPLETED: {mission.mission_id} - {requested_capability}"
        )
        return report

    def _handle_queue_execution(self, payload: Dict[str, Any]):
        """Callback from SafeActionQueue when MISSION_EXECUTION is APPROVED."""
        mission_id = payload.get("mission_id")
        mission = self.active_missions.get(mission_id)
        if not mission:
            # Queue consumers may run in a different process from the API/creator.
            # Reload persisted missions before declaring the action invalid.
            self._load_missions()
            mission = self.active_missions.get(mission_id)
        if not mission:
            dgm_logger.error(f"MISSION_EXECUTION_FAILED: {mission_id} - mission not found")
            raise ValueError(f"Mission not found: {mission_id}")

        if mission:
            try:
                dgm_logger.info(f"MISSION_EXECUTION_STARTED: {mission_id}")
                dgm_logger.info(f"MissionEngine: Queue execution triggered for {mission_id}")
                mission.logs.append("Action approved in SafeActionQueue. Starting execution.")

                if "lista" in mission.goal.lower() and "repos" in mission.goal.lower():
                    self._mark_execution_started(mission)
                    result = self._execute_list_repositories_mission(mission)
                    self._finish_mission_success(mission, result)
                    return result
                else:
                    capability = self._capability_request_from_goal(mission.goal)
                    if capability and "capability_discovery" not in mission.metadata:
                        self.discover_capability_for_mission(mission, capability)
                    dgm_logger.info(f"MISSION_HANDLER_SELECTED: {mission_id} - decompose_mission")
                    self.decompose_mission(mission_id)
                    return {
                        "status": "decomposed",
                        "mission_id": mission_id,
                        "capability_discovery": "performed" if capability else "not_requested",
                    }
            except Exception as exc:
                result = self._finish_mission_failure(mission, exc)
                raise RuntimeError(result["output"]) from exc

    def process_missions(self):
        """Consumer loop called by CognitionLoop."""
        for mission_id, mission in list(self.active_missions.items()):
            if mission.status == MissionStatus.COMPLETED or mission.status == MissionStatus.FAILED:
                continue

            # 1. Timeout Check
            if datetime.now() - mission.created_at > self.timeout_threshold:
                self._timeout_mission(mission, "Mission timed out before execution completed.")
                continue

            # 2. Lifecycle Transitions
            if mission.status == MissionStatus.CREATED:
                self._handle_created(mission)
            elif mission.status == MissionStatus.QUEUED:
                # Now handled by SafeActionQueue handler _handle_queue_execution
                pass
            elif mission.status == MissionStatus.APPROVAL_PENDING:
                self._handle_approval_pending(mission)
            elif mission.status == MissionStatus.RUNNING:
                if self._mission_execution_timed_out(mission):
                    self._timeout_mission(mission, "Mission execution exceeded 60 seconds.")
                    continue
                self._handle_running(mission)

    def _handle_created(self, mission: Mission):
        # This shouldn't normally be reached if create_mission already transitioned it
        dgm_logger.info(f"MISSION_QUEUED: {mission.mission_id}")
        mission.logs.append("Transitioning to QUEUED state.")
        self._update_status(mission, MissionStatus.QUEUED)

    def _handle_approval_pending(self, mission: Mission):
        # Legacy approval logic, keeping for compatibility but SafeActionQueue is now preferred
        req_id = mission.metadata.get("approval_request_id")
        if req_id:
            approval = self.approval_manager.approvals.get(req_id)
            # Check durable approval decision
            decision = mission.metadata.get("last_decision")
            approval_status = getattr(approval.get("status"), "value", None) if approval else None
            if decision == "approve" or approval_status == "approved":
                dgm_logger.info(f"MISSION_STARTED: {mission.mission_id}")
                mission.logs.append("User approved mission via legacy interface.")
                if "lista" in mission.goal.lower() and "repos" in mission.goal.lower():
                    self._mark_execution_started(mission)
                else:
                    self.decompose_mission(mission.mission_id)
            elif decision == "reject":
                dgm_logger.warning(f"MISSION_FAILED: {mission.mission_id} - Rejected by user")
                mission.logs.append("Mission rejected by user.")
                self._update_status(mission, MissionStatus.FAILED, {"error": "User rejected mission."})

    def _handle_running(self, mission: Mission):
        # Monitor subtasks if they exist
        if mission.subtasks:
            completed_tasks = [st for st in mission.subtasks if st.status == "completed"]
            mission.progress = len(completed_tasks) / len(mission.subtasks)

            if len(completed_tasks) == len(mission.subtasks):
                dgm_logger.info(f"MISSION_COMPLETED: {mission.mission_id}")
                mission.logs.append("All subtasks completed.")
                self._update_status(mission, MissionStatus.COMPLETED)
                return

        # Execute directly for specific goals that do not need subtasks.
        if not mission.subtasks and "lista" in mission.goal.lower() and "repos" in mission.goal.lower():
            try:
                result = self._execute_list_repositories_mission(mission)
                self._finish_mission_success(mission, result)
            except Exception as exc:
                self._finish_mission_failure(mission, exc)

    def _execute_list_repositories_mission(self, mission: Mission) -> Dict[str, Any]:
        dgm_logger.info(f"MISSION_HANDLER_SELECTED: {mission.mission_id} - list_repositories")
        started = time.monotonic()
        repositories, scan_meta = self._discover_workspace_repositories(started)
        output = self._render_repository_output(repositories)
        execution_duration = round(time.monotonic() - started, 3)
        result = {
            "mission_id": mission.mission_id,
            "handler": "list_repositories",
            "repositories": repositories,
            "count": len(repositories),
            "repos_scanned": scan_meta["repos_scanned"],
            "repos_skipped": scan_meta["repos_skipped"],
            "branches_truncated": scan_meta["branches_truncated"],
            "execution_duration": execution_duration,
            "summary": f"Found {len(repositories)} repositories.",
            "output": output,
            "generated_at": datetime.now().isoformat()
        }
        dgm_logger.info(f"MISSION_RESULT_GENERATED: {mission.mission_id} - {len(repositories)} repositories")
        return result

    def _discover_workspace_repositories(self, mission_started: float) -> tuple[List[Dict[str, Any]], Dict[str, Any]]:
        repositories: Dict[str, Dict[str, Any]] = {}
        repos_skipped = 0
        branches_truncated = 0

        for root in self.REPO_SCAN_ROOTS:
            if not root.exists():
                continue

            try:
                candidates = [p for p in root.iterdir() if p.is_dir()]
            except PermissionError:
                continue

            for path in sorted(candidates, key=lambda item: item.name.lower()):
                if time.monotonic() - mission_started >= self.MISSION_EXECUTION_TIMEOUT_SECONDS:
                    dgm_logger.error("MISSION_TIMEOUT: repository scan exceeded mission budget")
                    raise TimeoutError("Repository scan exceeded 60 seconds.")

                if not (path / ".git").exists():
                    continue

                key = str(path.resolve()).lower()
                if key in repositories:
                    continue

                if len(repositories) >= self.REPO_SCAN_LIMIT:
                    repos_skipped += 1
                    dgm_logger.warning(f"MISSION_REPO_SCAN_LIMIT: max repos scanned={self.REPO_SCAN_LIMIT}")
                    dgm_logger.info(f"MISSION_REPO_SCAN_SKIPPED: {path}")
                    continue

                repo_started = time.monotonic()
                repo = self._inspect_git_repository(path, repo_started, mission_started)
                if repo.get("branches_truncated"):
                    branches_truncated += 1
                repositories[key] = repo

        return (
            sorted(repositories.values(), key=lambda repo: repo["name"].lower()),
            {
                "repos_scanned": len(repositories),
                "repos_skipped": repos_skipped,
                "branches_truncated": branches_truncated,
            },
        )

    def _inspect_git_repository(self, path: Path, repo_started: float, mission_started: float) -> Dict[str, Any]:
        branch = self._run_git(path, ["branch", "--show-current"], repo_started, mission_started) or "detached"
        last_commit = self._run_git(path, ["rev-parse", "--short", "HEAD"], repo_started, mission_started) or "unknown"
        status_output = self._run_git(path, ["status", "--short"], repo_started, mission_started)
        branches = self._run_git(
            path,
            [
                "for-each-ref",
                f"--count={self.BRANCH_SCAN_LIMIT + 1}",
                "--format=%(refname:short)",
                "refs/heads",
                "refs/remotes",
            ],
            repo_started,
            mission_started,
        )
        branch_names = [line for line in branches.splitlines() if line.strip()]
        branches_truncated = len(branch_names) > self.BRANCH_SCAN_LIMIT
        if branches_truncated:
            branch_names = branch_names[:self.BRANCH_SCAN_LIMIT]
        changes = len([line for line in status_output.splitlines() if line.strip()]) if status_output else 0

        return {
            "name": path.name,
            "path": str(path),
            "branch": branch,
            "branches": branch_names,
            "branches_truncated": branches_truncated,
            "last_commit": last_commit,
            "uncommitted_changes": changes,
            "git_status": "dirty" if changes else "clean"
        }

    def _run_git(self, cwd: Path, args: List[str], repo_started: float, mission_started: float) -> str:
        try:
            now = time.monotonic()
            repo_remaining = self.REPO_TIMEOUT_SECONDS - (now - repo_started)
            mission_remaining = self.MISSION_EXECUTION_TIMEOUT_SECONDS - (now - mission_started)
            remaining = min(repo_remaining, mission_remaining)
            if remaining <= 0:
                dgm_logger.info(f"MISSION_REPO_SCAN_SKIPPED: {cwd} repo timeout")
                return ""

            result = subprocess.run(
                ["git", "-c", f"safe.directory={cwd}", *args],
                cwd=str(cwd),
                capture_output=True,
                text=True,
                timeout=max(0.1, remaining),
                check=False
            )
            if result.returncode != 0:
                return ""
            return result.stdout.strip()
        except Exception:
            return ""

    def _render_repository_output(self, repositories: List[Dict[str, Any]]) -> str:
        if not repositories:
            return "Found repositories: none"

        lines = ["Found repositories:"]
        for repo in repositories:
            lines.append(
                f"- {repo['name']} | branch={repo['branch']} | status={repo['git_status']} | "
                f"changes={repo['uncommitted_changes']} | last_commit={repo['last_commit']} | "
                f"branches_shown={len(repo.get('branches', []))}"
                f"{' truncated' if repo.get('branches_truncated') else ''} | path={repo['path']}"
            )
        return "\n".join(lines)

    def _mark_execution_started(self, mission: Mission):
        now = datetime.now()
        mission.metadata["execution_started_at"] = now.isoformat()
        mission.metadata["execution_timeout_seconds"] = self.MISSION_EXECUTION_TIMEOUT_SECONDS
        self._update_status(mission, MissionStatus.RUNNING)

    def _mission_execution_timed_out(self, mission: Mission) -> bool:
        started_at = mission.metadata.get("execution_started_at")
        if not started_at:
            return False
        try:
            started = datetime.fromisoformat(started_at)
        except ValueError:
            return False
        return (datetime.now() - started).total_seconds() > self.MISSION_EXECUTION_TIMEOUT_SECONDS

    def _timeout_mission(self, mission: Mission, reason: str):
        dgm_logger.error(f"MISSION_TIMEOUT: {mission.mission_id} - {reason}")
        self._finish_mission_failure(mission, TimeoutError(reason))

    def _finish_mission_success(self, mission: Mission, result: Dict[str, Any]):
        self._store_mission_result(mission, result)
        self._emit_mission_result(mission, result)
        self._update_status(mission, MissionStatus.COMPLETED, {"completed_at": datetime.now().isoformat()})
        dgm_logger.info(f"MISSION_EXECUTION_FINISHED: {mission.mission_id}")
        dgm_logger.info(f"MISSION_FORCE_COMPLETE: {mission.mission_id}")
        dgm_logger.info(f"MISSION_COMPLETED: {mission.mission_id}")

    def prepare_specialist_collaboration(
        self,
        mission_id: str,
        *,
        collaborator: str = "Claude Code Free",
        department: str = "ai-liaison",
        specialist_role: str = "external specialist reviewer",
        context: str = "",
        acceptance_criteria: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Prepare and persist a free-only handoff; never launches an external tool.

        The returned packet can be handed to a legitimate free browser session.
        Creating it is not provider authorization and performs no network call.
        """
        mission = self.active_missions.get(mission_id)
        if mission is None:
            raise KeyError(f"Mission not found: {mission_id}")

        help_record = mission.metadata.get("help_seeking", {})
        safe_context_parts = [mission.description.strip()]
        if context.strip():
            safe_context_parts.append(context.strip())
        if isinstance(help_record, dict) and help_record.get("help_request"):
            safe_context_parts.append("Existing help request:\n" + str(help_record["help_request"]))
        packet = self.collaboration_store.create_packet(
            goal=mission.goal,
            project=str(mission.metadata.get("project_id", "DGM-MAT")),
            department=department,
            specialist_role=specialist_role,
            collaborator=collaborator,
            context="\n\n".join(part for part in safe_context_parts if part),
            known_facts=mission.metadata.get("known_facts", []),
            attempted_steps=mission.logs[-10:],
            evidence=[
                f"mission_id={mission.mission_id}",
                f"mission_status={mission.status.value}",
                *( [f"mission_error={mission.error}"] if mission.error else [] ),
            ],
            constraints=[
                "FREE-ONLY; no paid API, subscription, upgrade, or credit spend",
                "If free capacity is exhausted, stop and wait; never use a paid fallback",
                "Do not include credentials, cookies, tokens, or private authentication data",
                "Do not modify DGM-MAT-FULL-MIRROR",
                "Changes require backup, tests, and independent review before promotion",
                "Do not expose the backend remotely before global HTTP/WebSocket security is complete",
            ],
            acceptance_criteria=acceptance_criteria or [
                "Return evidence-backed findings and a concrete next step",
                "Separate facts, assumptions, and unknowns",
                "Provide tests or a verification plan; do not claim tests that were not run",
                "Record reusable lessons only after independent validation",
            ],
        )
        mission.metadata["specialist_collaboration"] = {
            "collaboration_id": packet["collaboration_id"],
            "status": "PACKET_PREPARED_NO_EXTERNAL_CALL",
            "collaborator": collaborator,
            "free_only": True,
        }
        mission.logs.append(
            f"Specialist handoff packet prepared ({packet['collaboration_id']}); no external call or spending performed."
        )
        self.save_mission(mission)
        self._sync_state(mission)
        return packet

    def list_specialist_collaborations(self) -> List[Dict[str, Any]]:
        """Return a compact local status view; never contacts external providers."""
        return [
            {
                "collaboration_id": packet.collaboration_id,
                "goal": packet.goal,
                "project": packet.project,
                "department": packet.department,
                "specialist_role": packet.specialist_role,
                "collaborator": packet.collaborator,
                "status": packet.status.value,
                "updated_at": packet.updated_at,
                "blocked_reason": packet.blocked_reason,
            }
            for packet in self.collaboration_store.list_packets()
        ]

    def _mission_for_collaboration(self, collaboration_id: str) -> Optional[Mission]:
        for mission in self.active_missions.values():
            handoff = mission.metadata.get("specialist_collaboration", {})
            if isinstance(handoff, dict) and handoff.get("collaboration_id") == collaboration_id:
                return mission
        return None

    def pause_specialist_collaboration(self, collaboration_id: str, *, reason: str) -> Dict[str, Any]:
        """Persist a free-capacity pause without retrying, upgrading, or spending."""
        packet = self.collaboration_store.mark_waiting_for_free_capacity(
            collaboration_id, reason=reason
        )
        mission = self._mission_for_collaboration(collaboration_id)
        if mission:
            mission.metadata["specialist_collaboration"]["status"] = packet.status.value
            mission.metadata["specialist_collaboration"]["blocked_reason"] = packet.blocked_reason
            mission.logs.append(
                f"Specialist collaboration paused for free capacity ({collaboration_id}); no paid fallback."
            )
            self.save_mission(mission)
            self._sync_state(mission)
        return {
            "collaboration_id": packet.collaboration_id,
            "status": packet.status.value,
            "blocked_reason": packet.blocked_reason,
            "paid_fallback": False,
        }

    def record_specialist_result(
        self,
        collaboration_id: str,
        *,
        result: str,
        provenance: str,
    ) -> Dict[str, Any]:
        """Record collaborator output as untrusted and request independent QA review."""
        packet = self.collaboration_store.record_result(
            collaboration_id, result=result, provenance=provenance
        )
        mission = self._mission_for_collaboration(collaboration_id)
        if mission:
            mission.metadata["specialist_collaboration"]["status"] = packet.status.value
            mission.metadata["specialist_collaboration"]["review_required"] = True
            mission.logs.append(
                f"Specialist result received for {collaboration_id}; independent review required."
            )
            self.save_mission(mission)
            self._sync_state(mission)
        self.organization_bus.send(
            Message(
                sender_id="agent:hq-orchestrator",
                recipient_id="agent:bug-hunter",
                subject=f"Independent review required: {collaboration_id}",
                body=(
                    "A specialist collaboration result is stored as untrusted. Review the saved "
                    "record, inspect evidence, run appropriate local tests, and report findings. "
                    "Do not treat the result as accepted or promote a lesson before verification."
                ),
                mission_id=mission.mission_id if mission else None,
                priority=MessagePriority.HIGH,
                requires_response=True,
                correlation_id=collaboration_id,
            )
        )
        return {
            "collaboration_id": packet.collaboration_id,
            "status": packet.status.value,
            "review_required": True,
            "external_call_performed": False,
            "spending_performed": False,
        }

    def reject_specialist_result(
        self, collaboration_id: str, *, reviewer: str, reason: str
    ) -> Dict[str, Any]:
        packet = self.collaboration_store.reject_result(
            collaboration_id, reviewer=reviewer, reason=reason
        )
        mission = self._mission_for_collaboration(collaboration_id)
        if mission:
            mission.metadata["specialist_collaboration"]["status"] = packet.status.value
            mission.metadata["specialist_collaboration"]["review_required"] = False
            mission.logs.append(f"Specialist result rejected by independent review ({collaboration_id}).")
            self.save_mission(mission)
            self._sync_state(mission)
        return {
            "collaboration_id": packet.collaboration_id,
            "status": packet.status.value,
            "lesson_promoted": False,
        }

    def validate_specialist_result(
        self,
        collaboration_id: str,
        *,
        reviewer: str,
        review_notes: str,
        evidence: List[str],
        tests_passed: bool,
        reusable_lesson: str,
    ) -> Dict[str, Any]:
        """Validate reviewed output and persist a project-scoped lesson.

        The caller must run local verification and provide its real evidence.
        This method records that evidence; it does not execute arbitrary commands.
        """
        packet = self.collaboration_store.validate_result(
            collaboration_id,
            reviewer=reviewer,
            review_notes=review_notes,
            evidence=evidence,
            tests_passed=tests_passed,
            reusable_lesson=reusable_lesson,
        )
        lesson_status = "PERSISTED"
        lesson_id = None
        lesson_error = None
        try:
            lesson = self.validated_lesson_store.record(packet)
            lesson_id = lesson["lesson_id"]
        except Exception as exc:
            # The collaboration remains VALIDATED, but memory promotion is explicit and retryable.
            lesson_status = "PERSISTENCE_FAILED"
            lesson_error = type(exc).__name__
        mission = self._mission_for_collaboration(collaboration_id)
        if mission:
            mission.metadata["specialist_collaboration"]["status"] = packet.status.value
            mission.metadata["specialist_collaboration"]["review_required"] = False
            mission.metadata["specialist_collaboration"]["lesson_status"] = lesson_status
            if lesson_id:
                mission.metadata["specialist_collaboration"]["lesson_id"] = lesson_id
            if lesson_error:
                mission.metadata["specialist_collaboration"]["lesson_persistence_error"] = lesson_error
            mission.logs.append(
                f"Specialist result independently validated ({collaboration_id}); lesson persistence={lesson_status}."
            )
            self.save_mission(mission)
            self._sync_state(mission)
        return {
            "collaboration_id": packet.collaboration_id,
            "status": packet.status.value,
            "lesson_status": lesson_status,
            "lesson_id": lesson_id,
            "lesson_persistence_error": lesson_error,
            "external_call_performed": False,
            "spending_performed": False,
        }

    def retry_validated_lesson_persistence(self, collaboration_id: str) -> Dict[str, Any]:
        """Retry memory promotion after a prior storage failure, without revalidating."""
        packet = self.collaboration_store.get(collaboration_id)
        if packet.status.value != "VALIDATED":
            raise ValueError("Only a VALIDATED collaboration can retry lesson persistence")
        lesson = self.validated_lesson_store.record(packet)
        mission = self._mission_for_collaboration(collaboration_id)
        if mission:
            mission.metadata["specialist_collaboration"]["lesson_status"] = "PERSISTED"
            mission.metadata["specialist_collaboration"]["lesson_id"] = lesson["lesson_id"]
            mission.metadata["specialist_collaboration"].pop("lesson_persistence_error", None)
            mission.logs.append(f"Validated lesson persistence recovered ({collaboration_id}).")
            self.save_mission(mission)
            self._sync_state(mission)
        return {
            "collaboration_id": collaboration_id,
            "status": packet.status.value,
            "lesson_status": "PERSISTED",
            "lesson_id": lesson["lesson_id"],
        }

    def list_validated_specialist_lessons(self, *, project: str | None = None) -> List[Dict[str, Any]]:
        """Read only validated lessons from the local institutional learning ledger."""
        return self.validated_lesson_store.list_lessons(project=project)

    def _finish_mission_failure(self, mission: Mission, exc: Exception) -> Dict[str, Any]:
        output = f"Mission execution failed: {exc}"
        # Record a truthful, zero-cost next-step recommendation. This is advisory:
        # no retry, provider call, message dispatch, or spending occurs here.
        help_context = HelpContext(
            goal=mission.goal,
            unknowns=(f"{type(exc).__name__}: {exc}",),
            attempted_steps=tuple(mission.logs[-5:]),
            evidence=(f"mission_id={mission.mission_id}", f"exception_type={type(exc).__name__}"),
            max_attempts_reached=bool(mission.metadata.get("max_attempts_reached", False)),
        )
        help_decision = HelpSeekingPolicy.decide(help_context)
        mission.metadata["help_seeking"] = {
            "status": "RECOMMENDATION_ONLY",
            "action": help_decision.action.value,
            "reason": help_decision.reason,
            "next_step": help_decision.next_step,
            "help_request": help_decision.help_request,
            "spending_allowed": False,
        }
        # If the mission needs free investigation, prepare a reusable handoff packet.
        # This is local persistence only: no browser, provider call, or spending occurs.
        if (
            help_decision.action.value == "INVESTIGATE_FREE"
            and "specialist_collaboration" not in mission.metadata
        ):
            try:
                self.active_missions[mission.mission_id] = mission
                self.prepare_specialist_collaboration(mission.mission_id)
            except Exception as collaboration_error:
                # Fail closed without copying potentially sensitive exception text to logs.
                mission.metadata["specialist_collaboration"] = {
                    "status": "PACKET_PREPARATION_BLOCKED",
                    "reason": type(collaboration_error).__name__,
                    "free_only": True,
                }
                mission.logs.append(
                    "Specialist handoff preparation was blocked; no external call or spending performed."
                )
        mission.logs.append(
            f"Help-seeking recommendation recorded ({help_decision.action.value}); no automatic external call or spending performed."
        )
        started_at = mission.metadata.get("execution_started_at")
        execution_duration = 0.0
        if started_at:
            try:
                execution_duration = round((datetime.now() - datetime.fromisoformat(started_at)).total_seconds(), 3)
            except ValueError:
                execution_duration = 0.0
        result = {
            "mission_id": mission.mission_id,
            "handler": "mission_execution",
            "repositories": [],
            "count": 0,
            "repos_scanned": 0,
            "repos_skipped": 0,
            "branches_truncated": 0,
            "execution_duration": execution_duration,
            "summary": "Mission execution failed.",
            "output": output,
            "error": str(exc),
            "generated_at": datetime.now().isoformat()
        }
        self._store_mission_result(mission, result)
        self._emit_mission_result(mission, result)
        self._update_status(mission, MissionStatus.FAILED, {"error": str(exc), "completed_at": datetime.now().isoformat()})
        dgm_logger.error(f"MISSION_EXECUTION_FAILED: {mission.mission_id} - {exc}")
        return result

    def _store_mission_result(self, mission: Mission, result: Dict[str, Any]):
        mission.metadata["result"] = result
        mission.metadata["output"] = result["output"]
        mission.progress = 1.0
        mission.logs.append(result["output"])
        self.save_mission(mission)
        self._sync_state(mission)
        dgm_logger.info(f"MISSION_RESULT_STORED: {mission.mission_id}")

    def _emit_mission_result(self, mission: Mission, result: Dict[str, Any]):
        payload = {
            "type": "mission_result",
            "payload": result
        }
        safe_broadcast(payload)
        dgm_logger.info(f"MISSION_RESULT_EMITTED: {mission.mission_id}")

    def _update_status(self, mission: Mission, status: MissionStatus, metadata_update: Dict[str, Any] = None):
        mission.status = status
        mission.updated_at = datetime.now()
        if metadata_update:
            mission.metadata.update(metadata_update)
            if "error" in metadata_update:
                mission.error = metadata_update["error"]

        # Log status change in mission logs
        mission.logs.append(f"Status changed to {status.value}")

        self.save_mission(mission)
        self._sync_state(mission)

    def save_mission(self, mission: Mission):
        file_path = self.missions_path / f"{mission.mission_id}.json"
        data = {
            "mission_id": mission.mission_id,
            "goal": mission.goal,
            "description": mission.description,
            "status": mission.status.value,
            "metadata": mission.metadata,
            "created_at": mission.created_at.isoformat(),
            "updated_at": mission.updated_at.isoformat(),
            "progress": mission.progress,
            "logs": mission.logs,
            "error": mission.error
        }
        with open(file_path, "w") as f:
            json.dump(data, f, indent=4)

    def decompose_mission(self, mission_id: str) -> List[SubTask]:
        mission = self.active_missions.get(mission_id)
        if not mission or mission.status == MissionStatus.FAILED:
            return []

        subtasks = [
            SubTask(subtask_id=f"st_{uuid4().hex[:4]}", title="Analyze requirements", description=f"Analyze {mission.goal}"),
            SubTask(subtask_id=f"st_{uuid4().hex[:4]}", title="Execute implementation", description=f"Implement changes for {mission.goal}"),
            SubTask(subtask_id=f"st_{uuid4().hex[:4]}", title="Verify results", description=f"Verify {mission.goal}")
        ]
        mission.subtasks = subtasks
        mission.status = MissionStatus.RUNNING
        mission.progress = 0.0
        self.save_mission(mission)
        self._sync_state(mission)
        return subtasks

    def request_approval(self, mission_id: str, description: str) -> str:
        """Create a durable approval request; MissionEngine is not its authority."""
        request_id = f"req_{uuid4().hex[:6]}"
        approval = self.approval_manager.request_approval(request_id, description, 0.0, "LOW")
        mission = self.active_missions.get(mission_id)
        if mission:
            mission.metadata["approval_request_id"] = request_id
            mission.metadata["approval_action_id"] = approval.get("action_id") if isinstance(approval, dict) else None
            self.save_mission(mission)
            self._sync_state(mission)
        dgm_logger.info(f"APPROVAL_CREATED: {request_id} for mission {mission_id}")
        state_store.dispatch(StateEvents.APPROVAL_REQUESTED, {"request_id": request_id, "mission_id": mission_id, "description": description})
        return request_id

    def handle_approval_decision(self, request_id: str, decision: str):
        """Compatibility entry point delegating the decision to durable storage."""
        approval = self.approval_manager.approvals.get(request_id)
        if not approval:
            return False
        normalized = decision.lower()
        if normalized in {"approve", "approved"}:
            self.approval_manager.approve(request_id)
        elif normalized in {"reject", "rejected"}:
            self.approval_manager.reject(request_id)
        else:
            return False
        for mission in self.active_missions.values():
            if mission.metadata.get("approval_request_id") == request_id:
                mission.metadata["last_decision"] = decision
                self.save_mission(mission)
                self._sync_state(mission)
                break
        return True

    def _sync_state(self, mission: Mission):
        state_store.dispatch(StateEvents.MISSION_UPDATED, {
            "id": mission.mission_id,
            "mission_id": mission.mission_id,
            "goal": mission.goal,
            "status": mission.status.value,
            "updated_at": datetime.now().isoformat(),
            "progress": mission.progress,
            "logs": mission.logs,
            "error": mission.error,
            "metadata": mission.metadata,
            "result": mission.metadata.get("result"),
            "output": mission.metadata.get("output")
        })

mission_engine = MissionEngine()
