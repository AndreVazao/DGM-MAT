from scripts.autostart.sync_main_branches import relation


def test_main_sync_relation_classifies_fast_forward_states():
    assert relation(True, True) == "synced"
    assert relation(True, False) == "behind"
    assert relation(False, True) == "ahead_requires_review"
    assert relation(False, False) == "diverged_requires_review"
