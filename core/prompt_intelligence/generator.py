from typing import Dict, Any, List
import json

class PromptGenerator:
    def __init__(self, global_state_provider: Any):
        self.state_provider = global_state_provider

    def generate_prompt(self, gap_context: Dict[str, Any], provider: str = "default") -> str:
        ecosystem_state = self.state_provider.get_global_state()

        prompt = f"""# DGM-MAT EXTERNAL CONSULTATION REQUEST

## CONTEXT
You are assisting a self-learning autonomous multi-agent engineering system (DGM-MAT).
A knowledge gap has been detected during execution.

## ECOSYSTEM STATE SUMMARY
- Active Agents: {len(ecosystem_state.get('agents', {}))}
- Repositories: {list(ecosystem_state.get('repositories', {}).keys())}
- Evolution Chain Length: {ecosystem_state.get('evolution_chain_length', 0)}

## GAP DETAILS
- Category: {gap_context.get('category')}
- Description: {gap_context.get('description')}
- Source Agent: {gap_context.get('agent_id')}

## RELEVANT CONTEXT
{json.dumps(gap_context.get('context', {}), indent=2)}

## TASK
Analyze the provided information and provide a structured solution to bridge this knowledge gap.
If the gap is a missing implementation, provide the logic or code.
If it's an architectural decision, provide a recommendation with pros and cons.

## EXPECTED OUTPUT FORMAT
Provide your response in JSON format with the following fields:
- 'solution': Detailed explanation or code.
- 'integration_type': One of ['code_extension', 'architectural_decision', 'agent_capability'].
- 'impact': Estimated impact on the ecosystem.
- 'confidence': Your confidence score (0.0 to 1.0).

## CONSTRAINTS
- Adhere to DGM-MAT hub-and-spoke architecture.
- No direct agent-to-agent communication.
- All interactions must be event-driven via the Core Event Bus.
"""
        return prompt

    def optimize_for_provider(self, prompt: str, provider: str) -> str:
        # Simple provider-specific adjustments
        if provider == "claude":
            return f"Human: {prompt}\n\nAssistant:"
        elif provider == "chatgpt":
            return f"System: You are an expert engineer. {prompt}"
        return prompt
