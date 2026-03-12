# Critical Debater — Project Instructions
# Critical Debater — 项目指令

## Changelog / 变更日志

| 时间 / Time | 作者 / Author | 变更 / Change |
|---|---|---|
| 2026-03-12 | Codex | 统一为单技能 `critical-debater-suite`，新增 `skills-src` canonical source 和三平台导出（skills/.claude/openai） / Unified to single suite skill with canonical source and 3-platform outputs |
| 2026-03-12 | Claude | 新增系统架构文档 docs/system-architecture.md，包含流程图、信息流向、Agent 对比 / Added system architecture doc with flow diagrams, data flow, agent comparison |
| 2026-03-11 | Claude | 项目更名 Insight Debator → Critical Debater / Renamed project |
| 2026-03-11 | Claude | v0.5.0 升级：修复 6 个断开的 symlink，恢复 SKILL.md，全部 skill 统一版本号 / v0.5.0 upgrade: fix 6 broken symlinks, recover SKILL.md files, unify all skill versions |
| 2026-03-11 | Claude | v0.2.0 升级：Skills 合并到 .claude/skills/，移除 PDF 和 pre_mortem，动态 workspace 路径 / v0.2.0 upgrade: consolidated skills to .claude/skills/, removed PDF and pre_mortem, dynamic workspace paths |
| 2026-03-10 | Claude | 添加 v3 升级路线图引用 / Added v3 upgrade roadmap reference |
| 2026-03-09 | Claude | 初始创建：项目指令、工作方式、证据规则、agent 隔离、脚本引用 / Initial creation |

---

## Project Overview / 项目概述

Multi-agent debate system with 4 agents (Pro, Con, Judge, Orchestrator), 1 suite skill (v0.7.0), and file-based state management.
多 agent 辩论系统：4 个 agent、1 个套件 skill（v0.7.0）、基于文件的状态管理。

**Current version / 当前版本:** v0.7.0 — Single suite skill (`critical-debater-suite`) with canonical source in `skills-src/` and generated bundles in `skills/`, `.claude/skills/`, `openai/skills/`.

Design spec: `docs/debate_system_v2.md`
**System architecture: `docs/system-architecture.md`** — 完整流程图、信息流向、读写权限、Skill 分布、状态机（每次重大更新需同步更新）
v3 upgrade roadmap: `docs/upgrade-roadmap-v3.md`
v0.2.0 upgrade plan: `docs/upgrade-plan-v0.2.0.md`
v0.6.0 upgrade plan: `docs/upgrade-plan-v0.6.0.md`
v3 task prompts: `docs/tasks/phase-{1,2,3,4}-*.md`

## Working Approach / 工作方式

1. **LLM first / LLM 优先** — 阅读、判断、总结、分类、提取、论证构建、因果审计 → 全部用 LLM
2. **Existing skill second / 现有 skill 其次** — 复用项目内 1 个 suite skill（内部路由到 9 个 capability 模块）
3. **Deterministic code last / 确定性代码最后** — 仅用于 `scripts/` 中的操作：workspace 初始化、JSON 验证、hash、审计日志追加

## Evidence Rules / 证据规则

### Two Evidence Tracks / 两条证据轨道
- **Fact Track / 事实轨道**: 当前状态声明，来源过期 → status 降级为 `stale`
- **Reasoning Track / 推理轨道**: 历史、机制、趋势，**永不**自动降级。`freshness_status = timeless`

### Real-Time Capability / 实时能力
系统必须能获取最近 24h 内的信息。这是能力要求，不是证据年龄限制。

### Twitter/X Policy (v3 enhanced)
Signal layer only. Twitter-only claims → 永远不能成为 `verified`，需至少一个独立非社交来源。
v3: SourceIngest 对 Twitter 来源进行 LLM 假新闻预筛（`social_credibility_flag`），高风险来源自动提升验证优先级。

### Cross-Source Verification / 跨来源验证
Critical claims → 至少 2 个独立来源。Judge 独立重新验证，不信任辩手的单次引用。

## Reasoning Model / 推理模型

Every argument chain:
```
Observed facts → Mechanism → Scenario implication → Trigger conditions → Falsification conditions
```
攻击因果链，不仅攻击立场。每轮更新假设状态。

## Agent Isolation / Agent 隔离

| Agent | Read | Write |
|---|---|---|
| pro-debater | evidence_store, 上轮 judge_ruling | rounds/round_N/pro_turn.json |
| con-debater | evidence_store, pro_turn, 上轮 judge_ruling | rounds/round_N/con_turn.json |
| neutral-judge | pro_turn, con_turn, evidence_store, claim_ledger | rounds/round_N/judge_ruling.json |
| debate-orchestrator | 全部 | 全部 |

## Scripts Reference / 脚本引用

| Script | Usage |
|---|---|
| `scripts/init-workspace.sh <dir> <topic> <rounds>` | 创建 workspace 目录 + 初始化空 JSON |
| `scripts/validate-json.sh <file> <schema_type>` | 验证 JSON 必需字段 |
| `scripts/hash-snippet.sh <text>` | SHA-256 hash |
| `scripts/append-audit.sh <audit_file> <json_line>` | 原子追加 JSONL |

## Data Contracts / 数据契约

See `skills/critical-debater-suite/references/data-contracts.md` for all JSON schemas.

## Bilingual / 双语

All documents and outputs include both Chinese and English.
所有文档和输出包含中英文。
