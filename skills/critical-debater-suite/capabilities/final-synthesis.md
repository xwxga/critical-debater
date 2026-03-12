# Capability: Final Synthesis

Use when user asks to generate final report.

## Workflow
1. Aggregate evidence, claims, and round rulings.
2. Produce `reports/final_report.json` with required keys.
3. Produce `reports/debate_report.md` with substantive narrative.
4. Validate JSON and ensure markdown report exists and is non-empty.
5. Log report generation via `scripts/append-audit.sh`.
