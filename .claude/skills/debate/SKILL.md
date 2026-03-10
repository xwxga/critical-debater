---
name: debate
description: >
  Start a multi-agent debate on any topic. Use this skill when the user says
  "debate", "start a debate", "run a debate on", "argue about", or provides
  a topic they want analyzed from multiple perspectives with evidence verification.
  启动多agent辩论系统。
version: 0.1.0
---

# /debate — Multi-Agent Debate System
# /debate — 多Agent辩论系统

You are launching the Insight Debator multi-agent debate system.
你正在启动 Insight Debator 多 agent 辩论系统。

## Arguments / 参数

The user invoked this command with: $ARGUMENTS

Parse the arguments:
- **First argument**: debate topic (required, quoted string) / 辩论话题（必需）
- **Second argument**: number of rounds (optional, default 3) / 回合数（可选，默认 3）

Examples:
- `/debate "Bitcoin will surpass gold as store of value"` → topic, rounds = 3
- `/debate "Remote work increases productivity" 5` → topic, rounds = 5

## Execution / 执行

Launch the `debate-orchestrator` agent to drive the entire workflow:

1. Use the Agent tool to spawn a `debate-orchestrator` subagent with this prompt:

```
Run a full multi-agent debate.

Topic: <parsed topic>
Rounds: <parsed rounds>
Project root: <current working directory>

Follow your system prompt to execute all 4 phases:
1. Initialize workspace (run scripts/init-workspace.sh, gather evidence via WebSearch/WebFetch)
2. Run <N> debate rounds (Pro → Con → Judge each round, using Agent tool for each)
3. Generate final synthesis report
4. Offer scheduled refresh setup

Key references:
- Data contracts: .claude/skills/source-ingest/references/data-contracts.md
- Project rules: .claude/CLAUDE.md
- Scripts: scripts/init-workspace.sh, scripts/validate-json.sh, scripts/hash-snippet.sh, scripts/append-audit.sh

Present the final report in a readable, bilingual (Chinese + English) format to the user.
```

2. When the orchestrator completes, present its final report output to the user.

## Notes / 注意事项

- The debate runs sequentially within each round: Pro → Con → Judge
- Each agent runs as an isolated subagent via the Agent tool
- Pro and Con use Sonnet for cost efficiency; Judge uses Opus for verification accuracy
- All state is persisted to `debate-workspace/` as JSON files
- The system guarantees real-time information access (can fetch data from last 24 hours)
- Evidence chains may span any timeframe — historical evidence is valid
- No total scores — output uses evidence states (verified, contested, unverified, stale)
