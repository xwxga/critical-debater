# Three-Agent Real-Time Debate System (Workflow-First) — v2
# 三Agent实时辩论系统（工作流优先） — v2

## Changelog / 变更日志

| 时间 / Time | 作者 / Author | 变更 / Change |
|---|---|---|
| 2026-03-09 | Claude | v2 初稿：基于 v1 审查重写。修正 24h 语义、新增 Orchestrator Agent、Skill 拆分为 8 个中等粒度、新增 Agent 定义规范、Agent-Skill Binding、通信协议、基础设施映射、成本策略、错误处理。/ v2 initial draft: rewrite based on v1 review. Fixed 24h semantics, added Orchestrator Agent, 8 medium-granularity Skills, Agent definitions, Agent-Skill Binding, communication protocol, infrastructure mapping, cost strategy, error handling. |

---

## 1. Project Positioning / 项目定位

This project builds **agent + skill workflows** on top of the **Claude Code ecosystem**, not traditional software-first architecture.
本项目基于 **Claude Code 生态** 构建 **agent + skill 工作流**，不是传统软件优先架构。

Decision order for all tasks / 所有任务的决策顺序：

1. **LLM first / LLM 优先** — If the task is reading, judging, summarizing, classifying, extracting, or making decisions about content, use LLM.
   凡是涉及阅读、判断、总结、分类、提取、内容决策的，用 LLM。
2. **Existing skill & ecosystem second / 现有 skill 和生态其次** — Reuse Claude Code tools (WebSearch, WebFetch, Agent tool), MCP servers (Playwright, Supabase), and established patterns (code-review multi-agent, ralph-loop) before writing new code.
   复用 Claude Code 工具、MCP 服务器和已有模式，再写新代码。
3. **Deterministic code last / 确定性代码最后** — Only for things LLM/skills cannot do: file I/O, scheduling, time-window math, API orchestration, hashing.
   只写 LLM/skill 做不了的：文件 IO、调度、时间窗口计算、API 编排、哈希。

---

## 2. Goal and Success Criteria / 目标与成功标准

### Goal / 目标

Run multi-round debates on a user topic with four agents:
就用户话题运行多轮辩论，使用四个 agent：

- **Pro** — strictly supports the motion / 严格支持议题
- **Con** — strictly opposes the motion / 严格反对议题
- **Judge** — neutral verifier / 中立验证者
- **Orchestrator** — workflow driver and state manager / 工作流驱动器和状态管理器

### Success Criteria / 成功标准

- Conclusions are traceable to sources and timestamps. / 结论可追溯到来源和时间戳。
- System guarantees real-time information access (can always fetch data from the last 24 hours). / 系统保证实时信息获取能力（始终能获取最近 24 小时内的数据）。
- Evidence chains themselves may span any timeframe — historical data, long-term trends, and classical theories are valid evidence. / 证据链本身可跨越任何时间跨度——历史数据、长期趋势、经典理论都是合法证据。
- Critical factual claims require cross-source confirmation. / 关键事实性声明需要跨来源确认。
- Judge performs independent second-pass verification. / Judge 执行独立的二次验证。
- No user-facing total score; output uses evidence states. / 不面向用户展示总分；输出使用证据状态。

---

## 3. Agent Roles / Agent 角色

### 3.1 Pro Agent / 正方 Agent
- Always supports the motion. / 始终支持议题。
- Must rebut opponent points and add new arguments each round. / 每轮必须反驳对手观点并添加新论点。
- Every factual claim must attach evidence references. / 每个事实性声明必须附加证据引用。

### 3.2 Con Agent / 反方 Agent
- Always opposes the motion. / 始终反对议题。
- Same structure and constraints as Pro. / 与 Pro 相同的结构和约束。

### 3.3 Judge Agent / 裁判 Agent
- Never takes sides. / 从不偏向任何一方。
- Verifies citations, timeliness, and reasoning quality. / 验证引用、时效性和推理质量。
- Produces structured ruling and mandatory response points for the next round. / 产出结构化裁定和下一轮的必答点。

### 3.4 Orchestrator Agent / 编排 Agent（v2 新增）
- Drives the entire debate workflow. / 驱动整个辩论工作流。
- Initializes debate parameters (topic, rounds, horizon). / 初始化辩论参数。
- Sequences agent execution: Pro → Con → Judge per round. / 按顺序调度 agent 执行。
- Enforces mandatory response to Judge's unresolved points. / 强制回应 Judge 的未解决点。
- Manages claim ledger state and evidence freshness. / 管理声明账本状态和证据时效性。
- Triggers final report generation and scheduled refreshes. / 触发最终报告生成和定时刷新。

---

## 4. Agent Definitions / Agent 定义规范

Each agent follows Claude Code agent framework conventions.
每个 agent 遵循 Claude Code agent 框架规范。

### 4.1 pro-debater

```yaml
name: pro-debater
description: >
  Debate agent that strictly supports the motion.
  Use this agent when the orchestrator needs a pro-side argument for a debate round.
  <example>User topic: "Bitcoin will surpass gold as store of value" → pro-debater builds supporting argument chain</example>
  <example>Judge flagged weak causal link → pro-debater must strengthen or replace the argument</example>
model: sonnet
tools: [WebSearch, WebFetch, Read, Write]
```

### 4.2 con-debater

```yaml
name: con-debater
description: >
  Debate agent that strictly opposes the motion.
  Use this agent when the orchestrator needs a con-side argument for a debate round.
  <example>User topic: "Bitcoin will surpass gold as store of value" → con-debater builds opposing argument chain</example>
  <example>Judge flagged unsupported analogy → con-debater must address or concede the point</example>
model: sonnet
tools: [WebSearch, WebFetch, Read, Write]
```

### 4.3 neutral-judge

```yaml
name: neutral-judge
description: >
  Neutral verifier that audits both sides' evidence and reasoning quality.
  Use this agent after Pro and Con have completed their turns in a round.
  <example>Pro cited a 3-day-old article as current fact → Judge checks freshness and may downgrade</example>
  <example>Con used correlation as causation → Judge flags causal validity issue</example>
model: opus
tools: [WebSearch, WebFetch, Read, Write, Grep]
```

### 4.4 debate-orchestrator

```yaml
name: debate-orchestrator
description: >
  Workflow driver for the debate system. Manages round sequencing, state persistence, and final output.
  Use this agent to start a new debate or continue an ongoing one.
  <example>User says "debate whether remote work increases productivity" → orchestrator initializes and runs</example>
  <example>6-hour refresh triggered → orchestrator re-ingests sources and checks for evidence state changes</example>
model: sonnet
tools: [Read, Write, Glob, Grep, Agent, WebSearch]
```

---

## 5. Agent-Skill Binding / Agent-Skill 绑定

Each agent has access to specific skills. This prevents role bleed and enforces separation of concerns.
每个 agent 只能访问特定 skill，防止角色越界，强制职责分离。

| Agent | Skills | Rationale / 原因 |
|---|---|---|
| `pro-debater` | SourceIngest, DebateTurn, AnalogySafeguard | Needs evidence gathering and argument construction / 需要证据收集和论证构建 |
| `con-debater` | SourceIngest, DebateTurn, AnalogySafeguard | Same capabilities as Pro, symmetric design / 与 Pro 对称设计 |
| `neutral-judge` | JudgeAudit, EvidenceVerify, FreshnessCheck | Needs independent verification, must NOT share source ingestion with debaters / 需要独立验证，不与辩手共享来源获取 |
| `debate-orchestrator` | ClaimLedgerUpdate, FinalSynthesis, all orchestration logic | Manages state and output, does not argue or verify / 管理状态和输出，不参与论证或验证 |

---

## 6. Source System: Real-Time Capability and Evidence Tracks / 来源系统：实时能力与证据轨道

### 6.1 Real-Time Information Guarantee / 实时信息保证

The system **must** be capable of fetching information published within the last 24 hours at any point during the debate. This is a **capability requirement**, not a restriction on evidence age.
系统**必须**能在辩论的任何时刻获取最近 24 小时内发布的信息。这是一个**能力要求**，不是对证据年龄的限制。

### 6.2 Two Evidence Tracks / 两条证据轨道

- **Fact Track (Current State Claims) / 事实轨道（当前状态声明）：** Used for claims about the present situation (e.g., "BTC price is $X", "Company Y just announced Z"). Sources for these claims should be recent; if the source for a current-state claim is outdated, the claim's status is downgraded to `stale`.
  用于关于当前状态的声明。如果当前状态声明的来源已过时，声明状态降级为 `stale`。

- **Reasoning Track (Historical/Mechanism/Trend) / 推理轨道（历史/机制/趋势）：** Used for mechanism explanation, historical precedent, long-term trends, and classical theories. **No freshness constraint.** These are valid evidence in reasoning chains regardless of age.
  用于机制解释、历史先例、长期趋势和经典理论。**无时效限制。** 这些在推理链中是合法证据，不受年龄影响。

### 6.3 Twitter/X Policy / Twitter/X 政策

- Role: **signal layer only** (auxiliary evidence). / 角色：**仅信号层**（辅助证据）。
- A Twitter factual claim cannot be upgraded to verified fact without at least one independent non-social source. / Twitter 事实性声明未经至少一个独立非社交来源确认不能升级为已验证事实。
- Persist fields: `tweet_id`, `author_id`, `created_at`, `captured_at`, `url`, `text_hash`. / 持久化字段如左。

### 6.4 Core Verification Rules / 核心验证规则

- Critical claim → at least two independent sources. / 关键声明 → 至少两个独立来源。
- Current-state evidence with outdated source → `stale`. / 当前状态证据的来源过期 → `stale`。
- Historical/mechanism evidence → **never** auto-downgraded to stale. / 历史/机制证据 → **永不**自动降级为 stale。
- Judge reruns verification independently (do not trust debaters' single-pass citations). / Judge 独立重新验证（不信任辩手的单次引用）。

---

## 7. Reasoning Model / 推理模型

Every argument must follow a reasoning chain / 每个论点必须遵循推理链：

```
Observed facts → Mechanism → Scenario implication → Trigger conditions → Falsification conditions
观察到的事实 → 机制 → 场景推演 → 触发条件 → 证伪条件
```

Required behavior / 必需行为：
- Debaters attack each other's **causal chain**, not only stance. / 辩手攻击对方的**因果链**，而非仅攻击立场。
- Each round updates assumptions: upheld, weakened, invalidated. / 每轮更新假设状态：维持、削弱、无效。
- Judge audits causal validity (e.g., correlation ≠ causation). / Judge 审计因果有效性。

---

## 8. Historical / Classical Citations (Divergence with Control) / 历史/经典引用（受控使用）

- Historical/classical references are explanation-layer only. / 历史/经典引用仅用于解释层。
- Per-round share is capped (preferred <15% of content). / 每轮占比上限（建议 <15%）。
- Any analogy must include: / 任何类比必须包含：
  - At least 2 similarities / 至少 2 个相似点
  - At least 1 key structural difference / 至少 1 个关键结构差异
- Judge may mark analogy as "heuristic only" if invalid. / Judge 可将无效类比标记为"仅启发性"。

---

## 9. Core Skills (~8 Medium-Granularity) / 核心 Skill（~8 个中等粒度）

Skills are composable building blocks that agents invoke. Each skill has a clear input/output contract.
Skill 是 agent 调用的可组合构建块。每个 skill 有明确的输入/输出契约。

### Source Layer / 来源层

#### 9.1 SourceIngest
**Purpose / 用途：** Search, fetch, and normalize sources into `EvidenceItem` format.
搜索、抓取并将来源规范化为 `EvidenceItem` 格式。

- **Input:** topic keywords, search scope, time range (optional)
- **Output:** `EvidenceItem[]`
- **Underlying tools / 底层工具：** WebSearch, WebFetch, Playwright MCP (for JavaScript-heavy pages)
- **Behavior:** Searches multiple sources, fetches content, normalizes into structured evidence items with `credibility_tier` assignment.

#### 9.2 FreshnessCheck
**Purpose / 用途：** Validate real-time capability and check timeliness of current-state claims.
验证实时能力并检查当前状态声明的时效性。

- **Input:** `EvidenceItem[]`, claim context (current-state vs. historical/mechanism)
- **Output:** Each item tagged with `freshness_status` (`current` | `stale` | `timeless`)
- **Rules:**
  - Current-state claims with outdated sources → `stale`
  - Historical/mechanism/trend evidence → `timeless` (never auto-downgraded)
  - System capability check: can we still fetch <24h-old data right now?

### Verification Layer / 验证层

#### 9.3 EvidenceVerify
**Purpose / 用途：** Cross-source verification, credibility scoring, and Twitter signal validation.
跨来源验证、可信度评分和 Twitter 信号验证。

- **Input:** `ClaimItem` with `evidence_ids[]`
- **Output:** Updated `ClaimItem.status`, verification notes, confidence level
- **Rules:**
  - Critical claims require ≥2 independent sources
  - Twitter-only claims cannot become `verified`
  - Assigns `credibility_tier` to each source

#### 9.4 ClaimLedgerUpdate
**Purpose / 用途：** Manage claim state machine transitions.
管理声明状态机转换。

- **Input:** `ClaimItem`, new evidence or verification results
- **Output:** Updated `ClaimItem` with new `status` and `last_verified_at`
- **State machine:** `unverified` → `verified` | `contested` | `stale`
- **Persistence:** Writes to claim ledger file (JSON)

### Debate Layer / 辩论层

#### 9.5 DebateTurn
**Purpose / 用途：** Construct argument chain, generate rebuttals, attach evidence.
构建论证链、生成反驳、附加证据。

- **Input:** topic, side (pro/con), opponent's last arguments, Judge's mandatory response points, available evidence
- **Output:** Structured debate turn with reasoning chain, evidence references, rebuttals
- **Enforces:** Reasoning model (§7), mandatory response to Judge points

#### 9.6 AnalogySafeguard
**Purpose / 用途：** Validate historical analogy compliance.
验证历史类比合规性。

- **Input:** Debate turn content, analogy sections
- **Output:** Pass/fail per analogy, content share percentage
- **Rules:** ≥2 similarities, ≥1 structural difference, <15% content share

### Judge Layer / 裁判层

#### 9.7 JudgeAudit
**Purpose / 用途：** Independent verification, causal chain audit, structured ruling.
独立验证、因果链审计、结构化裁定。

- **Input:** Pro turn, Con turn, claim ledger, evidence store
- **Output:** `JudgeRuling` with verification results, causal validity flags, mandatory response points for next round
- **Behavior:** Reruns source verification independently (does NOT trust debaters' citations), checks correlation≠causation, identifies unresolved points

### Output Layer / 输出层

#### 9.8 FinalSynthesis
**Purpose / 用途：** Generate final report with watchlist and scenario outlook.
生成终报，包含监控清单和情景展望。

- **Input:** All rounds' data, claim ledger, evidence store
- **Output:** `FinalReport` (verified facts, probable conclusions, contested points, to_verify, scenario outlook, 24h watchlist with reversal triggers)

---

## 10. Agent Communication & State Management / Agent 通信与状态管理

### 10.1 Communication Protocol / 通信协议

Agents communicate through **shared file-based state** (inspired by ralph-loop pattern).
Agent 通过**共享文件状态**进行通信（参照 ralph-loop 模式）。

```
debate-workspace/
├── config.json                  # debate parameters (topic, rounds, horizon)
├── evidence/
│   └── evidence_store.json      # all EvidenceItems
├── claims/
│   └── claim_ledger.json        # all ClaimItems with status
├── rounds/
│   ├── round_1/
│   │   ├── pro_turn.json        # Pro's structured argument
│   │   ├── con_turn.json        # Con's structured argument
│   │   └── judge_ruling.json    # Judge's ruling + mandatory points
│   ├── round_2/
│   │   └── ...
│   └── round_N/
├── reports/
│   └── final_report.json        # FinalReport output
└── logs/
    └── audit_trail.jsonl        # append-only audit log
```

### 10.2 Agent Isolation / Agent 隔离

- Each agent runs as a **Claude Code subagent** (via Agent tool), providing natural context isolation.
  每个 agent 作为 **Claude Code subagent** 运行（通过 Agent tool），提供天然的上下文隔离。
- Agents can only read/write files in their permitted scope:
  Agent 只能读写其权限范围内的文件：
  - Pro/Con: read opponent's previous turn + judge ruling; write own turn
  - Judge: read both turns + evidence store; write ruling
  - Orchestrator: read/write everything

### 10.3 State Persistence / 状态持久化

- **Primary:** JSON files in workspace directory (simple, debuggable, version-controllable)
  **主要方式：** 工作区目录中的 JSON 文件（简单、可调试、可版本控制）
- **Audit trail:** Append-only JSONL log for all state changes
  **审计日志：** 只追加的 JSONL 日志记录所有状态变化
- **Optional upgrade path:** Supabase MCP for persistent cross-session storage if needed
  **可选升级路径：** 如需跨会话持久化可使用 Supabase MCP

---

## 11. Round Workflow (Orchestrator-Driven) / 回合工作流（编排驱动）

The Orchestrator Agent drives each step. This is NOT a static description — it is the Orchestrator's execution plan.
编排 Agent 驱动每一步。这不是静态描述，而是编排者的执行计划。

### Phase 1: Initialization / 初始化
1. Orchestrator receives topic, round count, and parameters.
   编排者接收话题、回合数和参数。
2. Orchestrator runs `SourceIngest` to gather initial evidence.
   编排者运行 `SourceIngest` 收集初始证据。
3. Orchestrator runs `FreshnessCheck` to tag evidence freshness.
   编排者运行 `FreshnessCheck` 标记证据时效性。
4. Orchestrator initializes `claim_ledger.json` and `evidence_store.json`.
   编排者初始化声明账本和证据存储。

### Phase 2: Debate Rounds / 辩论回合
For each round (1 to N):

1. **Orchestrator** prepares round context: opponent's last turn, Judge's mandatory points, current evidence.
   **编排者**准备回合上下文。
2. **Orchestrator** launches `pro-debater` subagent with `DebateTurn` skill.
   **编排者**启动 `pro-debater` 子 agent。
3. **Orchestrator** validates Pro output (mandatory response check).
   **编排者**验证 Pro 输出（必答点检查）。
4. **Orchestrator** launches `con-debater` subagent with `DebateTurn` skill.
   **编排者**启动 `con-debater` 子 agent。
5. **Orchestrator** validates Con output (mandatory response check).
   **编排者**验证 Con 输出。
6. **Orchestrator** launches `neutral-judge` subagent with `JudgeAudit` skill.
   **编排者**启动 `neutral-judge` 子 agent。
7. **Orchestrator** runs `ClaimLedgerUpdate` based on Judge ruling.
   **编排者**根据 Judge 裁定运行 `ClaimLedgerUpdate`。
8. **Orchestrator** logs round results to audit trail.
   **编排者**将回合结果记录到审计日志。

### Phase 3: Final Output / 最终输出
1. **Orchestrator** runs `FinalSynthesis` to generate the report.
   **编排者**运行 `FinalSynthesis` 生成报告。
2. **Orchestrator** outputs the final report.
   **编排者**输出最终报告。

### Phase 4: Scheduled Refresh / 定时刷新
- **Orchestrator** creates a scheduled task (every 6 hours recommended) via `mcp__scheduled-tasks__create_scheduled_task`.
  **编排者**通过 Scheduled Tasks 创建定时任务（建议每 6 小时）。
- On trigger: re-run `SourceIngest` + `FreshnessCheck` + `EvidenceVerify`.
  触发时：重新运行来源获取 + 时效检查 + 证据验证。
- If evidence state changes detected → regenerate report.
  如检测到证据状态变化 → 重新生成报告。

---

## 12. Infrastructure Mapping (Claude Code Ecosystem) / 基础设施映射（Claude Code 生态）

Map each system capability to concrete Claude Code ecosystem components.
将每个系统能力映射到具体的 Claude Code 生态组件。

| System Capability / 系统能力 | Claude Code Component / Claude Code 组件 | Notes / 备注 |
|---|---|---|
| Web search for evidence | **WebSearch** (built-in) | Primary source discovery / 主要来源发现 |
| Web page content fetch | **WebFetch** (built-in) | Article content extraction / 文章内容提取 |
| JavaScript-heavy page scraping | **Playwright MCP** | For dynamic content that WebFetch can't reach / 用于 WebFetch 无法获取的动态内容 |
| Agent isolation | **Agent tool** (subagent) | Each debater/judge runs as isolated subagent / 每个辩手/裁判作为隔离子 agent 运行 |
| Multi-agent orchestration pattern | **Code-review plugin pattern** | Reference: parallel agents + confidence scoring / 参考：并行 agent + 置信度评分 |
| Iterative improvement loop | **Ralph-loop pattern** | File-based state + iterative refinement across rounds / 基于文件的状态 + 跨回合迭代改进 |
| Scheduled refresh | **Scheduled Tasks MCP** (`mcp__scheduled-tasks__*`) | 6h cron job for evidence refresh / 6 小时定时任务刷新证据 |
| State persistence | **File system** (JSON files) | Simple, debuggable; upgrade to Supabase if needed / 简单可调试；按需升级到 Supabase |
| Audit logging | **File system** (JSONL append) | Append-only audit trail / 只追加审计日志 |
| Fact verification (external) | **Google Fact Check API**, **WebSearch** | Optional: external verification augmentation / 可选：外部验证增强 |

---

## 13. Data Contracts / 数据契约

### EvidenceItem

```json
{
  "evidence_id": "string",
  "source_type": "web | twitter | academic | government | other",
  "url": "string",
  "publisher": "string",
  "published_at": "ISO8601",
  "retrieved_at": "ISO8601",
  "snippet": "string",
  "hash": "string (SHA-256 of snippet)",
  "credibility_tier": "tier1_authoritative | tier2_reputable | tier3_general | tier4_social",
  "freshness_status": "current | stale | timeless",
  "evidence_track": "fact | reasoning"
}
```

### ClaimItem

```json
{
  "claim_id": "string",
  "round": "number",
  "speaker": "pro | con",
  "claim_type": "fact | inference | analogy",
  "claim_text": "string",
  "evidence_ids": ["string"],
  "status": "verified | contested | unverified | stale",
  "last_verified_at": "ISO8601",
  "judge_note": "string",
  "mandatory_response": "boolean (set by Judge)"
}
```

### JudgeRuling

```json
{
  "round": "number",
  "verification_results": [
    {
      "claim_id": "string",
      "original_status": "string",
      "new_status": "string",
      "reasoning": "string"
    }
  ],
  "causal_validity_flags": [
    {
      "claim_id": "string",
      "issue": "string (e.g., correlation≠causation)",
      "severity": "critical | moderate | minor"
    }
  ],
  "mandatory_response_points": [
    {
      "target": "pro | con | both",
      "point": "string",
      "reason": "string"
    }
  ],
  "round_summary": "string"
}
```

### FinalReport

```json
{
  "topic": "string",
  "total_rounds": "number",
  "generated_at": "ISO8601",
  "verified_facts": ["string"],
  "probable_conclusions": ["string with confidence qualifier"],
  "contested_points": ["string with both sides' positions"],
  "to_verify": ["string with suggested verification method"],
  "scenario_outlook": {
    "base_case": "string",
    "upside_triggers": ["string"],
    "downside_triggers": ["string"],
    "falsification_conditions": ["string"]
  },
  "watchlist_24h": [
    {
      "item": "string",
      "reversal_trigger": "string",
      "monitoring_source": "string"
    }
  ]
}
```

---

## 14. Output Format (User-Facing) / 输出格式（面向用户）

No total score. Use: / 不使用总分。使用：

- **Verified Facts / 已验证事实** — cross-source confirmed / 跨来源确认
- **High-Probability Conclusions / 高概率结论** — with confidence qualifiers / 附带置信度限定
- **Contested Points / 争议点** — both sides' best arguments / 双方最佳论点
- **Items Requiring Verification / 待验证项** — with suggested methods / 附带建议验证方法
- **Scenario Outlook / 情景展望** — base case + triggers + falsification conditions / 基准情景 + 触发条件 + 证伪条件
- **24h Watchlist / 24 小时监控清单** — items + reversal triggers + monitoring sources / 监控项 + 逆转触发条件 + 监控来源

---

## 15. Cost & Model Strategy / 成本与模型策略（v2 新增）

### Model Selection per Agent / 各 Agent 模型选择

| Agent | Model | Rationale / 原因 |
|---|---|---|
| `pro-debater` | Sonnet | Good reasoning at lower cost; argument construction is well within Sonnet capability / 良好推理，较低成本 |
| `con-debater` | Sonnet | Symmetric with Pro / 与 Pro 对称 |
| `neutral-judge` | Opus | Highest accuracy for verification and causal audit; Judge quality is the quality bottleneck / 最高准确度用于验证和因果审计 |
| `debate-orchestrator` | Sonnet | Orchestration logic doesn't require Opus-level reasoning / 编排逻辑不需要 Opus 级推理 |

### Token Budget Guidelines / Token 预算指导

- Per debate turn (Pro or Con): ~2,000-4,000 output tokens
- Per Judge audit: ~3,000-5,000 output tokens (more thorough)
- Per round total (including search): ~15,000-25,000 tokens
- 3-round debate estimated total: ~50,000-80,000 tokens
- Cost optimization: Sonnet for debaters reduces cost by ~5x vs all-Opus

---

## 16. Error Handling & Fallbacks / 错误处理与回退（v2 新增）

| Scenario / 场景 | Fallback / 回退策略 |
|---|---|
| Search returns no results / 搜索无结果 | Broaden keywords, try alternative search angles; if still empty, note "insufficient evidence" in claim ledger / 拓宽关键词，尝试其他搜索角度；仍无结果则在声明账本中注明"证据不足" |
| All current-state sources are outdated / 所有当前状态来源已过期 | Mark affected claims as `stale`; note in final report that current-state conclusions are provisional / 将受影响声明标记为 `stale`；在终报中注明当前状态结论为暂定 |
| Agent produces hallucinated citation / Agent 产生幻觉引用 | Judge's independent verification catches it — unverified claim stays `unverified`; log as audit event / Judge 独立验证捕获——未验证声明保持 `unverified`；记录为审计事件 |
| Agent fails to respond to mandatory point / Agent 未回应必答点 | Orchestrator detects missing response; re-prompts agent with explicit instruction; after 2 failures, log as "unaddressed" and proceed / 编排者检测缺失回应；重新提示 agent；2 次失败后记录为"未回应"并继续 |
| WebFetch/Playwright fails / 网页获取失败 | Retry once; if still fails, skip source and note in evidence store; never block the debate for a single source / 重试一次；仍失败则跳过来源并在证据存储中注明；不因单个来源阻塞辩论 |

---

## 17. Acceptance Criteria / 验收标准

- At least 3 rounds run end-to-end. / 至少 3 轮端到端运行。
- Stable structured outputs each round (valid JSON matching data contracts). / 每轮稳定结构化输出（匹配数据契约的有效 JSON）。
- No critical claim enters `verified` without cross-source validation. / 没有关键声明在未经跨来源验证的情况下进入 `verified`。
- Current-state claims with outdated sources are downgraded to `stale`; historical/mechanism evidence is NOT auto-downgraded. / 来源过期的当前状态声明降级为 `stale`；历史/机制证据不自动降级。
- Twitter-only claims cannot directly become verified facts. / 仅 Twitter 来源的声明不能直接成为已验证事实。
- Final report includes scenario triggers and falsification conditions. / 终报包含情景触发条件和证伪条件。
- Orchestrator enforces mandatory response to Judge's unresolved points. / 编排者强制回应 Judge 的未解决点。
- All agent interactions logged in audit trail. / 所有 agent 交互记录在审计日志中。
- Scheduled refresh task is created and functional. / 定时刷新任务已创建且可用。

---

## 18. Non-Goals (v2) / 非目标

- No heavy frontend productization. / 不做重前端产品化。
- No large multi-topic distributed orchestration. / 不做大规模多话题分布式编排。
- No auto-execution of financial or geopolitical actions. / 不自动执行金融或地缘政治操作。
- No user-facing scoreboards. / 不做面向用户的计分板。
- No custom model fine-tuning. / 不做自定义模型微调。
- No real-time streaming UI. / 不做实时流式 UI。
