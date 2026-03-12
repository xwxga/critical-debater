<p align="center">
  <h1 align="center">🏛️ Critical Debater</h1>
  <p align="center">
    <strong>Multi-agent debate system powered by Claude Code</strong><br/>
    <strong>基于 Claude Code 的多 Agent 辩论系统</strong>
  </p>
  <p align="center">
    <a href="#quick-start--快速开始">Quick Start</a> •
    <a href="#architecture--架构">Architecture</a> •
    <a href="#skills--技能">Skills</a> •
    <a href="#data-flow--数据流">Data Flow</a>
  </p>
</p>

---

## What is this? / 这是什么？

Critical Debater is a structured multi-agent debate system that pits **Pro** and **Con** agents against each other on any topic, with an independent **Judge** verifying evidence and auditing causal reasoning — all orchestrated automatically.

Critical Debater 是一个结构化多 Agent 辩论系统。**正方**和**反方** Agent 就任意议题对辩，由独立**裁判**验证证据、审计因果推理，全程自动编排。

**Key features / 核心特性:**

- 🔍 **Real-time evidence** — Web search, source credibility tiering, Twitter fake-news pre-screen
- ⛓️ **Causal reasoning chains** — Every argument: Observed facts → Mechanism → Scenario → Trigger → Falsification
- ⚖️ **Independent judge** — Cross-source verification, causal validity flags, mandatory response points
- 📊 **10-dimension conclusion profiles** — Probability, confidence, consensus, reversibility, actionability...
- 🕐 **24h watchlist** — Monitor what could flip the conclusions overnight
- 📜 **Historical wisdom** — Structured historical parallels with honesty safeguards
- 🔴 **Red Team mode** — Risk assessment with attack/mitigation/verdict structure

---

## Quick Start / 快速开始

> Requires [Claude Code](https://docs.anthropic.com/en/docs/claude-code) CLI

```bash
# Clone
git clone https://github.com/xwxga/critical-debater.git
cd critical-debater

# Start a debate (just type naturally)
claude "/debate Bitcoin will surpass gold as a store of value within 10 years"

# With options
claude "/debate --rounds 3 --depth deep --mode red_team Will AI replace most knowledge workers by 2030?"
```

The system will:
1. 🔍 Search and ingest evidence from the web
2. 🟢 **Pro** builds arguments with reasoning chains
3. 🔴 **Con** rebuts with counter-evidence
4. ⚖️ **Judge** independently verifies claims and audits causal logic
5. 🔁 Repeat for N rounds
6. 📊 Generate final report with conclusions, watchlist, and Markdown report

系统会自动：搜索证据 → 正方论证 → 反方反驳 → 裁判独立验证 → 重复 N 轮 → 输出最终报告

---

## Architecture / 架构

```
┌─────────────────────────────────────────────────────┐
│                   Orchestrator                       │
│            (drives workflow, manages state)           │
└──────┬──────────────┬──────────────┬────────────────┘
       │              │              │
       ▼              ▼              ▼
┌────────────┐ ┌────────────┐ ┌────────────┐
│  Pro Agent │ │  Con Agent │ │   Judge    │
│  正方 Agent │ │  反方 Agent │ │   裁判     │
│            │ │            │ │            │
│ • Arguments│ │ • Rebuttals│ │ • Verify   │
│ • Evidence │ │ • Counter  │ │ • Causal   │
│ • Reasoning│ │   evidence │ │   audit    │
│   chains   │ │ • Reasoning│ │ • Mandatory│
│            │ │   chains   │ │   response │
└────────────┘ └────────────┘ └────────────┘
       │              │              │
       ▼              ▼              ▼
┌─────────────────────────────────────────────────────┐
│              File-Based State Management              │
│                                                       │
│  debates/<topic>-<timestamp>/                         │
│  ├── config.json          # Debate configuration      │
│  ├── evidence_store/      # Verified evidence items   │
│  ├── claim_ledger.json    # Claim state machine       │
│  ├── rounds/                                          │
│  │   ├── round_1/                                     │
│  │   │   ├── pro_turn.json                            │
│  │   │   ├── con_turn.json                            │
│  │   │   └── judge_ruling.json                        │
│  │   └── round_N/...                                  │
│  ├── reports/                                         │
│  │   ├── final_report.json                            │
│  │   └── debate_report.md  # EN + CN Markdown         │
│  └── logs/audit_trail.jsonl                           │
└─────────────────────────────────────────────────────┘
```

### Agent Isolation / Agent 隔离

| Agent | Reads | Writes |
|---|---|---|
| **Pro** | evidence_store, previous judge_ruling | `rounds/round_N/pro_turn.json` |
| **Con** | evidence_store, pro_turn, previous judge_ruling | `rounds/round_N/con_turn.json` |
| **Judge** | pro_turn, con_turn, evidence_store, claim_ledger | `rounds/round_N/judge_ruling.json` |
| **Orchestrator** | Everything | Everything |

---

## Skills / 技能

9 composable skills power the system:

| Skill | Purpose / 用途 |
|---|---|
| 🏛️ `debate` | Entry point — parse args, launch orchestrator / 入口：解析参数，启动编排 |
| 🔍 `source-ingest` | Web search → EvidenceItem normalization / 搜索 → 证据标准化 |
| ⏰ `freshness-check` | Tag evidence: current / stale / timeless / 时效标记 |
| ✅ `evidence-verify` | Cross-source verification + Twitter corroboration / 跨源验证 |
| 🎤 `debate-turn` | Build arguments with 5-element reasoning chains / 构建推理链论证 |
| 📜 `analogy-safeguard` | Validate historical analogy structure / 历史类比结构验证 |
| ⚖️ `judge-audit` | Independent verification + causal audit + ruling / 独立验证 + 因果审计 |
| 📋 `claim-ledger-update` | Claim state machine management / 声明状态机管理 |
| 📊 `final-synthesis` | Final report + conclusion profiles + Markdown / 最终报告生成 |

---

## Data Flow / 数据流

```
User: "/debate <topic>"
         │
         ▼
    ┌─────────┐     ┌──────────────┐     ┌────────────────┐
    │  debate  │────▶│ source-ingest│────▶│ evidence_store/│
    │  (entry) │     │ (web search) │     │  (JSON files)  │
    └─────────┘     └──────────────┘     └───────┬────────┘
                                                  │
         ┌────────────────────────────────────────┘
         │
         ▼  ×N rounds
    ┌──────────┐    ┌──────────┐    ┌────────────┐
    │ Pro Turn │───▶│ Con Turn │───▶│ Judge Audit│
    │(debate-  │    │(debate-  │    │(judge-audit│
    │ turn)    │    │ turn)    │    │ +evidence- │
    └──────────┘    └──────────┘    │  verify)   │
                                    └─────┬──────┘
                                          │
                                          ▼
                                   ┌──────────────┐
                                   │claim-ledger- │
                                   │   update     │
                                   └──────┬───────┘
                                          │
         ┌────────────────────────────────┘
         │  After all rounds
         ▼
    ┌───────────────┐    ┌─────────────────────┐
    │final-synthesis│───▶│ reports/             │
    │               │    │ ├─ final_report.json │
    │               │    │ └─ debate_report.md  │
    └───────────────┘    └─────────────────────┘
```

---

## Reasoning Model / 推理模型

Every argument must follow the 5-element reasoning chain:
每个论点必须遵循 5 要素推理链：

```
Observed facts  →  Mechanism  →  Scenario implication  →  Trigger conditions  →  Falsification conditions
   观察事实     →     机制     →      场景推演         →      触发条件        →       证伪条件
```

The Judge attacks **causal chains**, not just positions. This prevents shallow "I disagree" rebuttals.
裁判攻击的是**因果链**，不仅仅是立场。这避免了浅层的"我不同意"式反驳。

---

## Configuration / 配置

Arguments passed via `/debate`:

| Flag | Options | Default |
|---|---|---|
| `--rounds` | 1-6 | 3 |
| `--depth` | `quick` / `standard` / `deep` | `standard` |
| `--mode` | `balanced` / `red_team` | `balanced` |
| `--domain` | `geopolitics` / `tech` / `health` / `finance` / `general` | auto-detect |
| `--speculation` | `conservative` / `moderate` / `exploratory` | `moderate` |
| `--language` | `en` / `zh` / `bilingual` | `bilingual` |

---

## Output Example / 输出示例

```
debates/bitcoin-vs-gold-20260311/
├── config.json
├── evidence_store/
│   ├── evi_a1b2c3d4.json
│   └── evi_e5f6g7h8.json
├── claim_ledger.json
├── rounds/
│   ├── round_1/
│   │   ├── pro_turn.json      # 3 arguments + reasoning chains
│   │   ├── con_turn.json      # 3 rebuttals + counter-arguments
│   │   └── judge_ruling.json  # verification + causal audit
│   ├── round_2/...
│   └── round_3/...
├── reports/
│   ├── final_report.json      # Structured conclusions (English)
│   └── debate_report.md       # Human-readable (EN + CN)
└── logs/
    └── audit_trail.jsonl
```

---

## Tech Stack / 技术栈

- **Runtime**: [Claude Code](https://docs.anthropic.com/en/docs/claude-code) CLI + Agent tool
- **Agents**: Claude Sonnet (debaters) + Claude Opus (judge)
- **State**: File-based JSON — no database needed
- **Scripts**: Bash (workspace init, JSON validation, audit logging)
- **Skills**: 9 composable `.claude/skills/`, [Agent Skills](https://agentskills.io) open standard compliant, [skills.sh](https://skills.sh) compatible

---

## License

MIT-0

---

<p align="center">
  <sub>Built with Claude Code 🤖</sub>
</p>
