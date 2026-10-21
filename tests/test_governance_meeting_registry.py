from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from core.governance.meeting_registry import GovernanceMeetingRegistry


class GovernanceMeetingRegistryTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.path = Path(self.tempdir.name) / "meetings.json"
        self.registry = GovernanceMeetingRegistry(self.path)

    def tearDown(self):
        self.tempdir.cleanup()

    def create(self, **overrides):
        values = {
            "title": "Proposta de novo departamento",
            "meeting_type": "structural_department_change",
            "requested_by": "Laboratório",
            "participants": ["CEO", "Laboratório", "Programação"],
            "agenda": ["Necessidade", "Riscos", "Recursos"],
            "proposal": "Criar departamento após avaliação e aprovação.",
            "related_departments": ["Laboratório", "Programação"],
        }
        values.update(overrides)
        return self.registry.create_meeting(**values)

    def test_create_persists_and_can_be_read_by_new_registry(self):
        meeting = self.create()
        loaded = GovernanceMeetingRegistry(self.path).get_meeting(meeting["meeting_id"])
        self.assertEqual(loaded["status"], "scheduled")
        self.assertEqual(loaded["participants"], ["CEO", "Laboratório", "Programação"])
        self.assertEqual(loaded["history"][0]["event"], "meeting.created")

    def test_high_impact_meeting_requires_ceo_participant(self):
        with self.assertRaisesRegex(ValueError, "CEO participation"):
            self.create(participants=["Laboratório", "Programação"])

    def test_contributions_and_decision_need_ceo_approval(self):
        meeting = self.create()
        meeting_id = meeting["meeting_id"]
        self.registry.add_contribution(meeting_id, actor="Programação", content="Precisamos de capacidade adicional.", kind="risk")
        result = self.registry.record_decision(
            meeting_id,
            actor="Diretor de Programação",
            outcome="approved",
            rationale="A proposta tem mérito, sujeita a aval executivo.",
            action_plan="Preparar plano detalhado; não executar ainda.",
        )
        self.assertEqual(result["status"], "decision_pending")
        self.assertEqual(result["approval"]["status"], "pending")

        approved = self.registry.approve_decision(
            meeting_id, actor="CEO", approved=True, rationale="Aprovado para avançar para planeamento."
        )
        self.assertEqual(approved["status"], "decision_pending")
        self.assertEqual(approved["owner_approval"]["status"], "pending")
        self.assertEqual(approved["action_dispatch"]["status"], "awaiting_owner_approval")
        owner_approved = self.registry.approve_by_owner(
            meeting_id, actor="André", approved=True, rationale="OK final do André."
        )
        self.assertEqual(owner_approved["status"], "approved")
        self.assertEqual(owner_approved["action_dispatch"]["status"], "ready_for_governed_execution")
        self.assertIn("meeting.ceo_approval_recorded", [event["event"] for event in owner_approved["history"]])
        self.assertIn("meeting.owner_approval_recorded", [event["event"] for event in owner_approved["history"]])

    def test_non_ceo_cannot_approve(self):
        meeting = self.create()
        self.registry.record_decision(
            meeting["meeting_id"], actor="Diretor", outcome="approved", rationale="Proposta favorável."
        )
        with self.assertRaisesRegex(ValueError, "only the CEO"):
            self.registry.approve_decision(
                meeting["meeting_id"], actor="Diretor", approved=True, rationale="Não autorizado."
            )

    def test_corrupt_store_is_never_overwritten(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text("{broken", encoding="utf-8")
        with self.assertRaises(RuntimeError):
            self.registry.create_meeting(
                title="Teste", meeting_type="routine", requested_by="CEO",
                participants=["CEO"], agenda=["Rever"], proposal="Teste"
            )
        self.assertEqual(self.path.read_text(encoding="utf-8"), "{broken")


    def test_agent_hiring_is_not_automatically_a_human_approval_gate(self):
        meeting = self.create(meeting_type="hire_agent", participants=["CEO", "RH"])
        self.assertFalse(meeting["high_impact"])
        self.assertEqual(meeting["owner_approval"]["status"], "not_required")

    def test_owner_cannot_approve_before_ceo_endorsement(self):
        meeting = self.create()
        with self.assertRaisesRegex(ValueError, "CEO endorsement"):
            self.registry.approve_by_owner(
                meeting["meeting_id"], actor="André", approved=True, rationale="OK"
            )

if __name__ == "__main__":
    unittest.main()
