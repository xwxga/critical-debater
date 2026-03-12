---
name: debate
description: >
  Start a multi-agent debate on any topic. Use this skill when the user says
  "debate", "start a debate", "run a debate on", "argue about", or provides
  a topic they want analyzed from multiple perspectives with evidence verification.
  启动多agent辩论系统，支持证据验证、因果链分析和结构化裁定。
---
## Runtime Capability Contract / 运行时能力契约

Use the shared generic capability contract:

- `../_shared/references/capability-adapter.md`
- `../_shared/references/execution-envelope.md`
- `../_shared/references/debate-orchestrator.md`

Tool names in this skill are capability-level and provider-agnostic:
- `search`
- `fetch`
- `spawn_role`
- `validate_json`
- `append_audit`

Fallback policy:
- `search`: native -> adapter -> `evidence_gap` soft-failure with audit note
- `fetch`: native -> adapter -> `fetch_skipped` soft-failure with audit note
- `spawn_role`: native -> adapter -> serial role emulation (`pro -> con -> judge`)

Model policy:
- Use tier names only: `fast`, `balanced`, `deep`
- Map provider-specific model names to these tiers at runtime

## Changelog / 变更日志

| 时间 / Time | 作者 / Author | 变更 / Change |
|---|---|---|
| 2026-03-11 | Claude | v0.5.0: recovered from broken symlink, unified version / 从断开的 symlink 恢复，统一版本号 |

# /debate — Multi-Agent Debate System
# /debate — 多Agent辩论系统

You are launching the Critical Debater multi-agent debate system.
你正在启动 Critical Debater 多 agent 辩论系统。

## Arguments / 参数

The user invoked this command with: $ARGUMENTS

Parse the arguments:
- **First argument**: debate topic (required, quoted string) / 辩论话题（必需）
- **Remaining arguments**: optional flags in any order / 可选标志，顺序不限

Supported flags:
- `--domain <value>`: geopolitics | tech | health | finance | philosophy | culture | general (default: auto-infer from topic)
- `--depth <value>`: quick | standard | deep (default: standard)
- `--rounds <N>`: number of rounds (default: 3)
- `--mode <value>`: balanced | red_team (default: balanced)
- `--speculation <value>`: conservative | moderate | exploratory (default: moderate)
- `--output <value>`: full_report | executive_summary | decision_matrix (default: full_report)
- `--language <value>`: en | zh | bilingual (default: bilingual)
- `--focus <value>`: comma-separated focus areas (default: none)

Examples:
- `/debate "Bitcoin vs Gold as store of value"` → all defaults, domain auto-inferred as finance
- `/debate "React vs Vue" --domain tech --depth deep --speculation exploratory`
- `/debate "Is remote work productive?" --mode red_team --output executive_summary`
- `/debate "中东局势" --rounds 5 --focus "oil prices,shipping routes"`

**Auto-inference / 自动推断:** If `--domain` is not provided, use LLM to infer the most appropriate domain from the topic text. Include the inferred domain in the config.json passed to the orchestrator.

## Execution / 执行

Preferred executable entrypoint (generic runtime):

```bash
scripts/run-generic-debate.sh "<topic>" --rounds <N> --output <format> --language <lang>
```

This script invokes the real generic orchestrator implementation:

- `scripts/debate_orchestrator_generic.py` (phase-by-phase execution)
- writes per-step logs under `debates/<workspace>/logs/`
- enforces long-output validation gates by default
- runs in strict no-fallback mode by default (enable fallback only via `--allow-fallback`)

If your runtime supports role spawning, you may still launch a `debate-orchestrator` role. In Codex generic runtime, orchestration is executed locally by the script above with serial role simulation.

Workflow phases (implemented by orchestrator):

1. Initialize workspace + ingest evidence (`source-ingest` + `freshness-check`)
2. Run rounds (`debate-turn` pro -> `debate-turn` con -> `judge-audit`)
3. Update claim ledger (`claim-ledger-update`)
4. Generate final report (`final-synthesis`)

When the orchestrator completes, present `reports/final_report.json` and `reports/debate_report.md`.

### Mode: `red_team`

When `config.mode = "red_team"`, the debate structure changes:

- **Con agent becomes Red Team**: Instead of opposing a motion, it actively searches for risks, vulnerabilities, failure modes, and blind spots in the topic/plan.
- **Pro agent becomes Blue Team**: Instead of supporting a motion, it defends against Red Team attacks with mitigations, contingency plans, and risk acceptance rationale.
- **Judge agent**: Evaluates the SEVERITY and LIKELIHOOD of each identified risk, and the FEASIBILITY of proposed mitigations.

**Orchestrator prompt adjustment:**
```
Run a Red Team analysis.

Topic: <parsed topic>
Mode: red_team
...

IMPORTANT MODE CHANGE:
- Con agent's role: RED TEAM — find every possible risk, failure mode, vulnerability, and blind spot. Be creative and thorough. Think about edge cases, cascading failures, adversarial scenarios, and black swan events.
- Pro agent's role: BLUE TEAM — for each risk identified by Red Team, propose mitigations, assess residual risk, and provide risk acceptance rationale where mitigation is impractical.
- Judge's role: Assess each risk's severity (critical/high/medium/low) and likelihood (high/medium/low). Evaluate whether Blue Team's mitigations are feasible and sufficient.
```

## Notes / 注意事项

- The debate runs sequentially within each round: Pro → Con → Judge
- Each agent runs as an isolated subagent
- All state is persisted to the workspace directory as JSON files
- The system guarantees real-time information access (can fetch data from last 24 hours)
- Evidence chains may span any timeframe — historical evidence is valid
- No total scores — output uses evidence states (verified, contested, unverified, stale)
