# Critical Debater Suite

This single skill routes debate-related requests to the correct capability workflow.

## Routing

Route user intent to one capability and execute that workflow end-to-end:

- `debate` / `start debate` / `run debate`: use `capabilities/debate.md`
- `search evidence` / `ingest sources` / `build evidence store`: use `capabilities/source-ingest.md`
- `check freshness` / `stale vs timeless`: use `capabilities/freshness-check.md`
- `verify evidence` / `cross-check claims`: use `capabilities/evidence-verify.md`
- `generate turn` / `pro turn` / `con turn` / `rebuttal`: use `capabilities/debate-turn.md`
- `judge round` / `audit round` / `mandatory response points`: use `capabilities/judge-audit.md`
- `update claim ledger` / `claim status transitions`: use `capabilities/claim-ledger-update.md`
- `analogy check` / `historical analogy safeguards`: use `capabilities/analogy-safeguard.md`
- `final report` / `synthesis` / `watchlist`: use `capabilities/final-synthesis.md`
- any mixed request: pick the primary intent, then chain other capabilities in the required order.

## Required Contracts

- Shared schemas: `references/data-contracts.md`
- Debate orchestrator: `scripts/debate_orchestrator_generic.py`
- Workspace init: `scripts/init-workspace.sh`
- JSON validation: `scripts/validate-json.sh`
- Audit append: `scripts/append-audit.sh`
- Hash utility: `scripts/hash-snippet.sh`

## Execution Rules

- Real execution only; never fabricate sources or files.
- Keep all file writes inside the active workspace.
- Validate all JSON outputs against `references/data-contracts.md` via `scripts/validate-json.sh`.
- If a required capability is unavailable, fail clearly and include a fallback reason.
- Preserve claim IDs, evidence IDs, and audit trace consistency across steps.

## Minimal Example

See `examples/quickstart.md` for a one-command smoke flow and expected outputs.
