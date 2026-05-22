import sys
import os
import time
import json
from core.event_bus.bus import Event, EventBus
from core.ecosystem_state.manager import EcosystemStateManager
from core.gap_detection.detector import GapDetector
from core.agents.prompt_intelligence_agent import PromptIntelligenceAgent
from core.agents.provider_connector_agent import ProviderConnectorAgent
from core.knowledge_integration.processor import KnowledgeProcessor
from core.meta_reasoning.orchestrator import MetaReasoningOrchestrator
from core.memory.engine import MemoryEngine
from core.agents.base import BaseAgent

def run_phase7_test():
    print("--- STARTING DGM-MAT PHASE 7: PROMPT INTELLIGENCE + META-LEARNING TEST ---")

    # 1. Setup
    bus = EventBus()
    state_manager = EcosystemStateManager(bus)
    memory_engine = MemoryEngine("core/memory/storage_test")

    gap_detector = GapDetector(bus)
    pi_agent = PromptIntelligenceAgent("pi_agent", bus, state_manager)
    provider_agent = ProviderConnectorAgent("provider_agent", bus)
    knowledge_processor = KnowledgeProcessor(bus, memory_engine)
    meta_orchestrator = MetaReasoningOrchestrator(bus)

    worker_agent = BaseAgent("worker_1", "worker", bus)

    print("\n[TEST 1] Simulating a task that triggers a knowledge gap...")

    # Create a trace_id to track the loop
    trace_id = "test-learning-loop-123"

    # Original task that will fail
    original_task = Event(
        source="user",
        target="worker_1",
        type="task",
        payload={"task_type": "complex_calculation", "data": [1, 2, 3]},
        priority="medium",
        trace_id=trace_id
    )

    # Register for retry
    meta_orchestrator.register_task_for_retry(trace_id, original_task)

    # 2. Simulate failure due to missing knowledge
    failure_event = Event(
        source="worker_1",
        type="error",
        payload={
            "category": "missing_knowledge",
            "error": "Don't know how to perform complex_calculation",
            "context": {"required_library": "math_pro_plus"}
        },
        priority="high",
        trace_id=trace_id
    )

    print("\n[STEP] Publishing failure event...")
    bus.publish(failure_event)

    # 3. System Loop - Iteration 1: Gap Detection -> Prompt Generation -> External Request
    print("\n[STEP] Iteration 1: Gap Detection & Prompt Generation")
    bus.process_queue() # Process failure -> Gap detected
    bus.process_queue() # Process gap_detected -> External consultation request

    # 4. System Loop - Iteration 2: Provider handles request -> External response
    print("\n[STEP] Iteration 2: External Consultation")
    bus.process_queue() # Process external_consultation_request -> External consultation response

    # 5. System Loop - Iteration 3: Knowledge Processor handles response -> Knowledge Integrated
    print("\n[STEP] Iteration 3: Knowledge Integration")
    bus.process_queue() # Process external_consultation_response -> Knowledge integrated

    # 6. System Loop - Iteration 4: Meta-Reasoning retries original task & Agent upgrades
    print("\n[STEP] Iteration 4: Meta-Reasoning Retry & Agent Upgrade")
    # This might take multiple pops because multiple events are published (integrated knowledge + evolution + agent upgraded)
    while bus.queue:
        event = bus.process_queue()
        if event and event.type == "task" and event.payload.get("is_retry"):
            print(f"SUCCESS: Original task retried with new knowledge: {event.payload.get('new_knowledge')[:50]}...")
            break

    # Check if worker agent was upgraded
    if "bridge_logic" in str(worker_agent.capabilities):
         print("SUCCESS: Worker agent upgraded with new capability!")

    print("\n[TEST 2] Verifying Global State Evolution")
    state = state_manager.get_global_state()
    print(f"Evolution Chain Length: {state['evolution_chain_length']}")

    if state['evolution_chain_length'] > 0:
        print("SUCCESS: Evolution events recorded.")

    print("\n--- PHASE 7 TEST COMPLETE ---")

if __name__ == "__main__":
    run_phase7_test()
