import pytest
from core.federation.federation_engine import FederationEngine
from core.federation.federation_models import FederationMessage

def test_federation_handling():
    engine = FederationEngine()
    msg = FederationMessage(
        id="MSG-001",
        source_ecosystem="Labs",
        target_ecosystem="Core",
        payload={"task": "sync"},
        signature="valid"
    )
    engine.handle_federated_request(msg)
    # Success if no exception and logged correctly
