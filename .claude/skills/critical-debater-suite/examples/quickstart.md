# Quickstart

Run a minimal smoke debate from the skill bundle root:

```bash
bash scripts/run-generic-debate.sh "Remote work net productivity" --rounds 1 --min-evidence 3 --source-retries 1 --allow-fallback
```

Expected outputs:
- `debates/<topic>-<timestamp>/config.json`
- `debates/<topic>-<timestamp>/reports/final_report.json`
- `debates/<topic>-<timestamp>/reports/debate_report.md`
- `debates/<topic>-<timestamp>/logs/audit_trail.jsonl`
