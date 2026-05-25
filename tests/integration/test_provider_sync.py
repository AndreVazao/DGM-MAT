import sys
from core.operator.provider_sync import ProviderSync
from core.observability.logger import dgm_logger

def validate():
    dgm_logger.info("Validating Provider Sync...")
    sync = ProviderSync()

    # Test lineage tracking
    sync.track_prompt_lineage("PROMPT-1", "SYSTEM-A")
    if "PROMPT-1" in sync.prompt_lineage:
        dgm_logger.info("ProviderSync Lineage: SUCCESS")
    else:
        dgm_logger.error("ProviderSync Lineage: FAILED")
        return False

    # Test identity mapping
    sync.map_identity("GPT-USR-1", "DGM-USR-1")
    if sync.identity_map["GPT-USR-1"] == "DGM-USR-1":
        dgm_logger.info("ProviderSync Identity: SUCCESS")
    else:
        dgm_logger.error("ProviderSync Identity: FAILED")
        return False

    return True

if __name__ == "__main__":
    if validate():
        print("PROVIDER SYNC VALIDATION: PASSED")
    else:
        print("PROVIDER SYNC VALIDATION: FAILED")
        sys.exit(1)
