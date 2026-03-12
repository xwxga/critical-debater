# Capability: Debate Turn

Use when user asks for a pro/con turn or rebuttal generation.

## Workflow
1. Build arguments with evidence links and reasoning_chain.
2. Build rebuttals targeting opponent claim IDs.
3. Include mandatory_responses when judge points exist.
4. Include historical_wisdom and speculative_scenarios sections.
5. Validate output with `scripts/validate-json.sh` (pro_turn/con_turn).
