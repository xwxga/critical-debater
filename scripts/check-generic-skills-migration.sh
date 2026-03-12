#!/bin/bash
# check-generic-skills-migration.sh
# Quality gate for generic skills migration.

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

python3 scripts/validate-generic-skills.py --check-claude-unchanged

# Regression sanity against existing sample workspace outputs.
./scripts/validate-json.sh debate-workspace/config.json config
./scripts/validate-json.sh debate-workspace/evidence/evidence_store.json evidence_item
./scripts/validate-json.sh debate-workspace/claims/claim_ledger.json claim_item
./scripts/validate-json.sh debate-workspace/rounds/round_1/pro_turn.json pro_turn
./scripts/validate-json.sh debate-workspace/rounds/round_1/con_turn.json con_turn
./scripts/validate-json.sh debate-workspace/rounds/round_1/judge_ruling.json judge_ruling
./scripts/validate-json.sh debate-workspace/reports/final_report.json final_report

echo "OK: generic migration checks passed"
