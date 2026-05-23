from typing import Dict, Any, Optional
from core.recovery.recovery_models import CrashType, CrashSeverity

class CrashClassifier:
    def classify(self, error_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        error_msg = str(error_data.get("message", "")).lower()

        if "websocket" in error_msg or "disconnect" in error_msg:
            return {"type": CrashType.WEBSOCKET_DISCONNECT, "severity": CrashSeverity.MEDIUM}

        if "provider" in error_msg or "auth" in error_msg:
            return {"type": CrashType.PROVIDER_CRASH, "severity": CrashSeverity.HIGH}

        if "memory" in error_msg or "corruption" in error_msg:
            return {"type": CrashType.MEMORY_CORRUPTION, "severity": CrashSeverity.CRITICAL}

        return {"type": CrashType.RUNTIME_CRASH, "severity": CrashSeverity.HIGH}
