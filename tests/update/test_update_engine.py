from core.update.update_engine import UpdateEngine


def test_update_engine_does_not_claim_release_discovery():
    engine = UpdateEngine()

    assert engine.check_for_updates() is None


def test_update_engine_fails_closed_instead_of_claiming_update_success():
    engine = UpdateEngine()

    assert engine.apply_update("v0.2.0") is False
