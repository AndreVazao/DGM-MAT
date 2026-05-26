from typing import Dict, Any

class RemoteTaskSchema:
    def serialize_task(self, task: Dict[str, Any]) -> str:
        import json
        return json.dumps({
            "task_id": task["task_id"],
            "payload": task.get("metadata", {}),
            "source_node": "...",
            "target_capabilities": ["local_inference"]
        })
