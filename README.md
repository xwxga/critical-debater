# Critical Debater v2

Multi-agent adversarial debate system with real-time evidence verification, per-round evidence refresh, and structured bilingual report output.

## Features

- **4-Agent Architecture**: Pro, Con, Judge (independent verification), Orchestrator
- **Per-Round Evidence Refresh**: Each round searches for new evidence driven by judge feedback
- **Parallel Pro/Con**: Both sides argue independently each round — no information asymmetry
- **5-Element Reasoning Chains**: Every argument requires observed facts, mechanism, scenario, triggers, falsification
- **10-Dimension Conclusion Profiles**: Probability, confidence, consensus, evidence coverage, reversibility, validity window, impact, causal clarity, actionability, falsifiability
- **Bilingual Reports**: Full English + Chinese Markdown reports
- **Agent Skills Compatible**: Works with Claude Code, GPT/OpenClaw, Codex, skills.sh

## Quick Start

    debate "Should central banks adopt digital currencies?" --rounds 3 --depth standard

## Architecture

SubAgent pattern with file-based state machine. Orchestrator dispatches Pro/Con/Judge through sequential rounds with JSON file communication.

    Phase 1: Init → SourceIngest(broad) → FreshnessCheck
    Phase 2: Per round: [Evidence Refresh] → Pro || Con → Judge → ClaimLedger
    Phase 3: FinalSynthesis → debate_report.md

## Output

- `reports/final_report.json` — Structured JSON with all conclusions
- `reports/debate_report.md` — Bilingual Markdown report

## Spec

Full system specification: [docs/critical-debater-v2-spec.md](docs/critical-debater-v2-spec.md)

## License

MIT-0
