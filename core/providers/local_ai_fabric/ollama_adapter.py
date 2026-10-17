import httpx
from typing import Dict, Any, List, Optional
from core.observability.logger import dgm_logger

class OllamaAdapter:
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self.timeout = httpx.Timeout(10.0, connect=5.0)

    async def list_models(self) -> List[str]:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                if response.status_code == 200:
                    models = response.json().get("models", [])
                    return [m["name"] for m in models]
                return []
        except Exception as e:
            dgm_logger.error(f"OllamaAdapter: Failed to list models: {e}")
            return []

    async def generate(self, model: str, prompt: str) -> Optional[str]:
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(60.0, connect=10.0)) as client:
                payload = {
                    "model": model,
                    "prompt": prompt,
                    "stream": False
                }
                response = await client.post(f"{self.base_url}/api/generate", json=payload)
                if response.status_code == 200:
                    return response.json().get("response")
                return None
        except Exception as e:
            dgm_logger.error(f"OllamaAdapter: Generation failed: {e}")
            return None
