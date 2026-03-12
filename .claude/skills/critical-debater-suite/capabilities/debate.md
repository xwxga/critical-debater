# Capability: Debate Orchestration

Use when user asks to run a full multi-round debate.

## Inputs
- topic
- rounds (default 3)
- mode/depth/speculation/language/output options

## Workflow
1. Initialize workspace via `scripts/init-workspace.sh`.
2. Run source ingestion before round 1.
3. For each round: pro turn -> con turn -> judge audit -> claim ledger update.
4. Run final synthesis and write report artifacts.
5. Validate JSON outputs with `scripts/validate-json.sh`.

## Outputs
- `config.json`
- `evidence/evidence_store.json`
- `claims/claim_ledger.json`
- `rounds/round_N/{pro_turn.json,con_turn.json,judge_ruling.json}`
- `reports/{final_report.json,debate_report.md}`
- `logs/audit_trail.jsonl`
