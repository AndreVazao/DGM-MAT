from __future__ import annotations

import os
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from fastapi import HTTPException

from core.api.governance_api import (
    MeetingApprovalRequest,
    _require_governance_role,
    _trust_owner_actor,
    approve_governance_meeting,
    approve_governance_meeting_as_owner,
)


CEO_TOKEN = "test-ceo-governance-secret-" + ("c" * 40)
OWNER_TOKEN = "test-owner-governance-secret-" + ("o" * 40)


def request(*, credential: str = "", principal: dict | None = None):
    headers = {}
    if credential:
        headers["x-dgm-governance-credential"] = credential
    return SimpleNamespace(
        headers=headers,
        state=SimpleNamespace(dgm_principal=principal or {"subject": "local-operator", "session_id": "session-1", "scopes": ["operator"]}),
    )


class GovernanceApiAuthTests(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict(os.environ, {
            "DGM_GOVERNANCE_CEO_TOKEN": CEO_TOKEN,
            "DGM_GOVERNANCE_OWNER_TOKEN": OWNER_TOKEN,
        })
        self.env.start()
        self.addCleanup(self.env.stop)

    def test_privileged_roles_require_distinct_server_credentials(self):
        with self.assertRaises(HTTPException) as caught:
            _require_governance_role(
                request(principal={"role": "owner", "username": "andrevazao"}),
                "owner",
            )
        self.assertEqual(caught.exception.status_code, 403)

    def test_missing_or_equal_server_credentials_fail_closed(self):
        with patch.dict(os.environ, {
            "DGM_GOVERNANCE_CEO_TOKEN": "same-secret-" + ("x" * 40),
            "DGM_GOVERNANCE_OWNER_TOKEN": "same-secret-" + ("x" * 40),
        }):
            with self.assertRaises(HTTPException) as caught:
                _require_governance_role(request(credential=OWNER_TOKEN), "owner")
        self.assertEqual(caught.exception.status_code, 503)

    def test_valid_ceo_credential_records_ceo_not_client_actor(self):
        registry = Mock()
        registry.approve_decision.return_value = {"status": "decision_pending"}
        payload = MeetingApprovalRequest(actor="attacker-supplied-name", approved=True, rationale="Reviewed")
        with patch("core.api.governance_api._meeting_registry", return_value=registry):
            result = approve_governance_meeting("meeting-1", payload, request(credential=CEO_TOKEN))
        self.assertEqual(result["status"], "decision_pending")
        self.assertEqual(registry.approve_decision.call_args.kwargs["actor"], "CEO")

    def test_valid_owner_credential_records_owner_not_client_actor(self):
        registry = Mock()
        registry.approve_by_owner.return_value = {"status": "approved"}
        payload = MeetingApprovalRequest(actor="attacker-supplied-name", approved=True, rationale="Reviewed")
        with patch("core.api.governance_api._meeting_registry", return_value=registry):
            result = approve_governance_meeting_as_owner("meeting-1", payload, request(credential=OWNER_TOKEN))
        self.assertEqual(result["status"], "approved")
        self.assertEqual(registry.approve_by_owner.call_args.kwargs["actor"], "André")

    def test_owner_role_in_session_or_client_name_cannot_spoof_owner_approval(self):
        payload = MeetingApprovalRequest(actor="André", approved=True, rationale="Spoof attempt")
        spoofed = request(principal={"role": "owner", "username": "andrevazao", "session_id": "operator-session"})
        with self.assertRaises(HTTPException) as caught:
            approve_governance_meeting_as_owner("meeting-1", payload, spoofed)
        self.assertEqual(caught.exception.status_code, 403)

    def test_owner_role_in_session_cannot_spoof_progressive_trust(self):
        spoofed = request(principal={"role": "system_owner", "username": "andrevazao"})
        with self.assertRaises(HTTPException) as caught:
            _trust_owner_actor(spoofed)
        self.assertEqual(caught.exception.status_code, 403)

    def test_owner_credential_authorizes_trust_as_server_attributed_owner(self):
        self.assertEqual(_trust_owner_actor(request(credential=OWNER_TOKEN)), "André")

    def test_owner_credential_cannot_approve_as_ceo(self):
        payload = MeetingApprovalRequest(actor="CEO", approved=True, rationale="Wrong role")
        with self.assertRaises(HTTPException) as caught:
            approve_governance_meeting("meeting-1", payload, request(credential=OWNER_TOKEN))
        self.assertEqual(caught.exception.status_code, 403)


if __name__ == "__main__":
    unittest.main()
