import asyncio
from core.providers.performance.provider_routing_engine import ProviderRoutingEngine
from core.providers.chatgpt.chatgpt_provider import ChatGPTProvider
from core.providers.claude.claude_provider import ClaudeProvider
from core.observability.logger import dgm_logger

async def run_provider_stress():
    p1 = ChatGPTProvider()
    p2 = ClaudeProvider()
    router = ProviderRoutingEngine([p1, p2])

    dgm_logger.info("STRESS TEST: Simulating provider failover...")
    # Simulate p1 failure
    best = router.handle_failover("chatgpt")
    dgm_logger.info(f"STRESS TEST: Failover selected: {best.provider_id}")
    assert best.provider_id == "claude"

if __name__ == "__main__":
    asyncio.run(run_provider_stress())
