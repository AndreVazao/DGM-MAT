from __future__ import annotations

from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from core.api import dgm_hub_agents_api as api
from core.organization.dgm_hub_multichat_bridge import HubTaskResult\nfrom core.organization.specialist_collaboration import SpecialistCollaborationStore


class FakeEngine:
    def __init__(self, root):
        self.collaboration_store = SpecialistCollaborationStore(root)
        self.results = []
        self.paused = []

    def record_specialist_result(self, collaboration_id, *, result, provenance):
        packet = self.collaboration_store.record_result(
            collaboration_id, result=result, provenance=provenance
        )
        self.results.append((collaboration_id, result, provenance))
        return {
            "collaboration_id": collaboration_id,
            "status": packet.status.value,
            "review_required": True,
        }

    def pause_specialist_collaboration(self, collaboration_id, *, reason):
        packet = self.collaboration_store.mark_waiting_for_free_capacity(
            collaboration_id, reason=reason
        )
        self.paused.append((collaboration_id, reason))
        return {"collaboration_id": collaboration_id, "status": packet.status.value}

