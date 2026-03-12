# Capability: Claim Ledger Update

Use when user asks to persist claim state transitions.

## Workflow
1. Upsert claims extracted from pro/con arguments.
2. Apply judge verification results to status transitions.
3. Preserve prior rounds and append conflict_details when present.
4. Validate `claim_ledger.json` then append audit line.
