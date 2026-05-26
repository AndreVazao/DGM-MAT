import json
from typing import Dict, Any, Optional

class ProviderBase:
    """Base class for all provider adapters."""
    def parse_session_data(self, data: str) -> Optional[Dict[str, Any]]:
        if not data:
            return None
        try:
            # Use json.loads instead of eval - Phase 39 Hardening
            return json.loads(data)
        except json.JSONDecodeError:
            return None
