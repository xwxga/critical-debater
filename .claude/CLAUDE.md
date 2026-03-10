# Insight Debator — Project Instructions
# Insight Debator — 项目指令

## Changelog / 变更日志

| 时间 / Time | 作者 / Author | 变更 / Change |
|---|---|---|
| 2026-03-10 18:57 | Claude | Skill 跨平台迁移：skills 从 .claude/skills/ 移至 .agents/skills/，symlink 回 .claude/skills/，升级 frontmatter v0.3.0，兼容 ClawHub/OpenClaw/skills.sh / Cross-platform skill migration: canonical location moved to .agents/skills/, symlinked back, frontmatter upgraded to v0.3.0 |
| 2026-03-10 16:30 | Claude | 合并全局 CLAUDE.md 规则：语义优先、禁止硬编码、变更日志规则 / Merged global CLAUDE.md rules: semantic-first, no hardcoded examples, changelog rules |
| 2026-03-10 | Claude | 添加 v3 升级路线图引用 / Added v3 upgrade roadmap reference |
| 2026-03-09 | Claude | 初始创建：项目指令、工作方式、证据规则、agent 隔离、脚本引用 / Initial creation |

---

## Project Overview / 项目概述

Multi-agent debate system with 4 agents (Pro, Con, Judge, Orchestrator), 9 skills, and file-based state management.
多 agent 辩论系统：4 个 agent、9 个 skill、基于文件的状态管理。

Design spec: `docs/debate_system_v2.md`
v3 upgrade roadmap: `docs/upgrade-roadmap-v3.md`
v3 task prompts: `docs/tasks/phase-{1,2,3,4}-*.md`

### Skill Layout / Skill 目录结构
- **Canonical location / 规范位置**: `.agents/skills/<name>/SKILL.md` (cross-platform, compatible with ClawHub/OpenClaw/skills.sh)
- **Claude Code access / Claude Code 访问**: `.claude/skills/<name>` → symlink to `.agents/skills/<name>`
- **Shared resources / 共享资源**: `.agents/skills/_shared/references/data-contracts.md`
- **Setup script / 设置脚本**: `scripts/setup-skill-symlinks.sh` (creates .claude/skills/ symlinks, idempotent)

## Working Approach / 工作方式

1. **LLM first / LLM 优先** — 阅读、判断、总结、分类、提取、论证构建、因果审计 → 全部用 LLM
2. **Existing skill second / 现有 skill 其次** — 复用项目内 8 个 skill + Claude Code 内建工具（WebSearch, WebFetch, Agent tool）
3. **Deterministic code last / 确定性代码最后** — 仅用于 `scripts/` 中的操作：workspace 初始化、JSON 验证、hash、审计日志追加

Do NOT default to writing Python scripts for text tasks. Do NOT build static rule-based tools when LLM judgment is better.
不要默认用脚本处理文本任务。不要在 LLM 判断更好时构建静态规则工具。

## Semantic First, Never Mechanical / 语义优先，拒绝机械化

When generating intermediate artifacts (subtitles, summaries, segments, etc.), ALWAYS use natural semantic understanding first — then apply constraints.
生成中间产物（字幕、摘要、片段等）时，**永远先用自然语义理解，再施加约束**。

- NEVER use mechanical numeric rules (e.g. "5-15 words per entry") to split, merge, or chunk text. These produce mid-phrase breaks and garbage output.
  **绝不**用机械数字规则（如"每条5-15词"）来拆分、合并、分块文本。这会产生断在短语中间的垃圾输出。
- ALWAYS let LLM understand the full meaning first, then break at natural boundaries (sentence ends, speaker turns, logical pauses).
  **永远**让 LLM 先理解完整语义，再在自然边界处断开（句子结尾、说话人切换、逻辑停顿）。
- Numeric limits (word count, duration) are soft guidelines for the LLM, not hard mechanical rules for code to enforce.
  数字限制（词数、时长）是给 LLM 的软性参考，不是给代码强制执行的硬规则。

## No Hardcoded Examples / 不要硬编码特例

Never put session-specific or project-specific values into prompts or code as hardcoded examples. Write generic instructions that let LLM use context to figure it out. Hardcoded examples make code non-reusable and break on different inputs.
不要把当前会话或项目特有的值硬编码到 prompt 或代码中作为示例。写通用指令，让 LLM 根据上下文自行判断。硬编码的特例让代码无法复用，换个输入就会失效。

## Document Changelog Rule / 文档变更日志规则

Every time you update a document file (`.md`, design docs, architecture docs, project masters, etc.), you MUST add a changelog entry at the **top of the file** (right after the title).
每次更新文档类文件时，**必须**在文件顶部（标题之后）添加变更日志条目。

Format / 格式:
```
## Changelog / 变更日志

| 时间 / Time | 作者 / Author | 变更 / Change |
|---|---|---|
| newest first... |
```

Timestamp rules / 时间戳规则:
- Same-day updates: precision to **minute** (e.g. `2026-03-06 03:19`)
  日内更新：精确到**分钟**
- Cross-day updates: precision to **day** (e.g. `2026-03-06`)
  跨日更新：精确到**日**

New entries go at the top of the table (newest first). Never remove old entries.
新条目放表格最上方（最新优先）。不要删除旧条目。

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
| `scripts/setup-skill-symlinks.sh` | 创建 .claude/skills/ → .agents/skills/ 的 symlink |

## Data Contracts / 数据契约

See `.agents/skills/_shared/references/data-contracts.md` for all JSON schemas.
(Also accessible via symlink: `.claude/skills/source-ingest/references/data-contracts.md`)

## Bilingual / 双语

All documents and outputs include both Chinese and English.
所有文档和输出包含中英文。
