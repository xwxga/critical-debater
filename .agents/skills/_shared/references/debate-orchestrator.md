# debate-orchestrator (Generic Runtime)

This is the generic orchestrator definition used by Codex runtime.

Primary executable:

- `scripts/debate_orchestrator_generic.py`
- wrapper: `scripts/run-generic-debate.sh`

## Responsibilities

1. Initialize workspace (`scripts/init-workspace.sh`)
2. Ingest evidence (`source-ingest` + `freshness-check`)
3. Execute each round in order:
   - `debate-turn` (pro)
   - `debate-turn` (con)
   - `judge-audit` + `evidence-verify`
   - `claim-ledger-update`
4. Generate `final_report.json` + `debate_report.md` (`final-synthesis`)
5. Validate JSON outputs via `scripts/validate-json.sh`
6. Append audit events via `scripts/append-audit.sh`

## Runtime Policy

- Default mode: strict no-fallback.
- Optional degraded mode: `--allow-fallback`.
- Long output gate defaults:
  - `arguments >= 3` per side per round
  - `rebuttals >= 2` per side per round

## Artifacts

For workspace `debates/<topic>-<timestamp>/`:

- `config.json`
- `evidence/evidence_store.json`
- `claims/claim_ledger.json`
- `rounds/round_N/pro_turn.json`
- `rounds/round_N/con_turn.json`
- `rounds/round_N/judge_ruling.json`
- `reports/final_report.json`
- `reports/debate_report.md`
- `logs/audit_trail.jsonl`
- `logs/orchestrator_run.log`
