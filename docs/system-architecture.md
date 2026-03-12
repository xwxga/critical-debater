# Critical Debater — System Architecture
# Critical Debater — 系统架构

## Changelog / 变更日志

| 时间 / Time | 作者 / Author | 变更 / Change |
|---|---|---|
| 2026-03-12 | Claude | 初始创建：完整系统流程图、信息流向图、Agent 对比分析 / Initial creation: full system flow, data flow, agent pattern comparison |

---

## 1. Architecture Pattern / 架构模式

Critical Debater 采用 **SubAgent + 文件状态机** 模式，而非 Agent Teams。

### 三种 Agent 模式对比 / Agent Pattern Comparison

| 维度 | 本系统 (Custom SubAgent) | 原生 SubAgent | Agent Teams |
|---|---|---|---|
| **通信方式** | 文件 JSON (evidence_store, turns) | 返回值（一次性） | 直接消息传递 |
| **Agent 身份** | 有角色（Pro/Con/Judge） | 无（临时 worker） | 有（Team Lead + Teammates） |
| **状态持久** | 文件系统 | 无状态 | 各自 session |
| **Agent 间通信** | 必须经过 Orchestrator | 只能回报主 agent | 可以直接互通 |
| **并行执行** | 串行（Pro->Con->Judge） | 可并行 spawn | 天然并行 |
| **隔离控制** | 读写权限矩阵 | 靠 tools 列表 | 靠 git worktree |
| **成本** | 中（多轮 API 调用） | 低（一次性任务） | 高（多个独立 session） |
| **适合场景** | 结构化对抗工作流 | 探索、搜索、独立任务 | 大型并行开发 |

### 为什么选择 SubAgent 而非 Agent Teams / Why SubAgent Over Agent Teams

辩论是 **必须串行的对抗链**，不是可并行的独立任务：

```
Coding (适合 Agent Teams):     Debate (适合 SubAgent):
A ──→ output_A                 Pro ──→ pro_turn
B ──→ output_B                   ↓
C ──→ output_C                 Con ──→ con_turn (必须先读 Pro)
  ↓ merge                        ↓
 Done                          Judge ──→ ruling (必须先读 Pro + Con)
                                  ↓
                               下一轮 (必须先读 ruling)
```

---

## 2. 完整系统流程图 / Full System Flow

```
╔══════════════════════════════════════════════════════════════════════════════╗
║  用户输入 / User Input                                                       ║
║  /debate "Bitcoin vs Gold" --rounds 3 --mode balanced --depth standard       ║
╚════════════════════════════════╤═════════════════════════════════════════════╝
                                │
                    ┌───────────▼───────────┐
                    │   debate skill        │  <- .claude/skills/debate/SKILL.md
                    │   (入口 / Entry)       │
                    │                       │
                    │  解析参数 / Parse:     │
                    │  * topic: string      │
                    │  * --rounds: 3        │
                    │  * --mode: balanced   │
                    │  * --depth: standard  │
                    │  * --domain: auto     │
                    │  * --speculation: mod │
                    │  * --output: full     │
                    │  * --language: bi     │
                    └───────────┬───────────┘
                                │ spawn subagent
                                │ (Agent tool, type=debate-orchestrator)
                                ▼
╔══════════════════════════════════════════════════════════════════════════════╗
║  ORCHESTRATOR (debate-orchestrator.md)                                       ║
║  model: sonnet | tools: Read,Write,Glob,Grep,Agent,WebSearch,WebFetch,Bash  ║
║  角色: 工作流控制器 + 状态管理器 + 质量守门人                                     ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  ┌─────────────────────────────────────────────────────────────────────┐     ║
║  │ PHASE 1: 初始化 / Initialization                                    │     ║
║  │                                                                     │     ║
║  │  Step 1: 创建 workspace                                            │     ║
║  │  ┌─────────────────────────────────────────────────────────┐       │     ║
║  │  │ bash scripts/init-workspace.sh                          │       │     ║
║  │  │   "$WORKSPACE" "<topic>" <rounds>                       │       │     ║
║  │  │                                                         │       │     ║
║  │  │ 输出 / Creates:                                         │       │     ║
║  │  │   debates/<topic-slug>-<timestamp>/                     │       │     ║
║  │  │   ├── config.json          <- DebateConfig schema       │       │     ║
║  │  │   ├── evidence/                                         │       │     ║
║  │  │   │   └── evidence_store.json   (空 [])                 │       │     ║
║  │  │   ├── claims/                                           │       │     ║
║  │  │   │   └── claim_ledger.json     (空 [])                 │       │     ║
║  │  │   ├── rounds/                                           │       │     ║
║  │  │   │   ├── round_1/                                      │       │     ║
║  │  │   │   ├── round_2/                                      │       │     ║
║  │  │   │   └── round_3/                                      │       │     ║
║  │  │   ├── reports/                                          │       │     ║
║  │  │   └── logs/                                             │       │     ║
║  │  │       └── audit_trail.jsonl                             │       │     ║
║  │  └─────────────────────────────────────────────────────────┘       │     ║
║  │                                                                     │     ║
║  │  Step 2: SourceIngest (证据搜集)                                    │     ║
║  │  ┌─────────────────────────────────────────────────────────┐       │     ║
║  │  │ 技能: source-ingest skill                               │       │     ║
║  │  │                                                         │       │     ║
║  │  │ 输入 / Reads:                                           │       │     ║
║  │  │   * config.json -> topic, domain, depth                 │       │     ║
║  │  │   * depth 决定搜索量:                                    │       │     ║
║  │  │     quick=3 queries, standard=5, deep=8                 │       │     ║
║  │  │                                                         │       │     ║
║  │  │ 执行 / Does:                                            │       │     ║
║  │  │   * WebSearch x N (多角度搜索关键词)                      │       │     ║
║  │  │   * WebFetch (提取正文内容)                               │       │     ║
║  │  │   * hash-snippet.sh (SHA-256 -> evidence_id)            │       │     ║
║  │  │   * LLM: 领域可信度评估 (credibility_tier)               │       │     ║
║  │  │   * LLM: Twitter 假新闻预筛 (social_credibility_flag)    │       │     ║
║  │  │                                                         │       │     ║
║  │  │ 输出 / Writes:                                          │       │     ║
║  │  │   * evidence_store.json <- EvidenceItem[] schema         │       │     ║
║  │  │     每条含: evidence_id, source_type, url, snippet,     │       │     ║
║  │  │     hash, credibility_tier, evidence_track,             │       │     ║
║  │  │     social_credibility_flag, verification_priority      │       │     ║
║  │  └─────────────────────────────────────────────────────────┘       │     ║
║  │                                                                     │     ║
║  │  Step 3: FreshnessCheck (时效标注)                                  │     ║
║  │  ┌─────────────────────────────────────────────────────────┐       │     ║
║  │  │ 技能: freshness-check skill                             │       │     ║
║  │  │                                                         │       │     ║
║  │  │ 输入 / Reads:                                           │       │     ║
║  │  │   * evidence_store.json (全部 EvidenceItem)              │       │     ║
║  │  │                                                         │       │     ║
║  │  │ 执行 / Does:                                            │       │     ║
║  │  │   * LLM: 分类 evidence_track (fact vs reasoning)        │       │     ║
║  │  │   * 规则: fact track + 过期 -> stale                    │       │     ║
║  │  │   * 规则: reasoning track -> timeless (永不降级)         │       │     ║
║  │  │                                                         │       │     ║
║  │  │ 输出 / Updates:                                         │       │     ║
║  │  │   * evidence_store.json <- freshness_status 字段更新    │       │     ║
║  │  │     current | stale | timeless                          │       │     ║
║  │  └─────────────────────────────────────────────────────────┘       │     ║
║  │                                                                     │     ║
║  │  -> config.json: status = "evidence_gathered"                       │     ║
║  │  -> audit_trail.jsonl: action = "workspace_initialized"             │     ║
║  └─────────────────────────────────────────────────────────────────────┘     ║
║                                                                              ║
║                                                                              ║
║  ┌─────────────────────────────────────────────────────────────────────┐     ║
║  │ PHASE 2: 辩论回合 / Debate Rounds  (x N rounds)                    │     ║
║  │                                                                     │     ║
║  │  ╔═══════════════════════════════════════════════════════════╗      │     ║
║  │  ║  Round N (每轮重复 / Repeat per round)                    ║      │     ║
║  │  ╠═══════════════════════════════════════════════════════════╣      │     ║
║  │  ║                                                           ║      │     ║
║  │  ║  -- 2a. PRO-DEBATER ──────────────────────────────────   ║      │     ║
║  │  ║  | agent: pro-debater.md                               |  ║      │     ║
║  │  ║  | model: sonnet | tools: WebSearch,WebFetch,Read,     |  ║      │     ║
║  │  ║  |        Write,Bash                                   |  ║      │     ║
║  │  ║  | 角色: 严格支持正方                                    |  ║      │     ║
║  │  ║  |                                                     |  ║      │     ║
║  │  ║  | 输入 / Reads:                                       |  ║      │     ║
║  │  ║  |   [Y] evidence_store.json (全部证据)                 |  ║      │     ║
║  │  ║  |   [Y] claim_ledger.json (已有声明)                   |  ║      │     ║
║  │  ║  |   [Y] [round>1] round_N-1/judge_ruling.json         |  ║      │     ║
║  │  ║  |       -> mandatory_response_points (必须回应)        |  ║      │     ║
║  │  ║  |   [Y] [round>1] round_N-1/con_turn.json             |  ║      │     ║
║  │  ║  |       -> 对手上轮论点 (用于构建反驳)                  |  ║      │     ║
║  │  ║  |   [X] 不能读: 本轮 con_turn (还没写)                 |  ║      │     ║
║  │  ║  |                                                     |  ║      │     ║
║  │  ║  | 应用的 Skills:                                       |  ║      │     ║
║  │  ║  |   * debate-turn skill (构建论点)                     |  ║      │     ║
║  │  ║  |   * analogy-safeguard skill (验证类比)               |  ║      │     ║
║  │  ║  |   * evidence-verify skill (可选，补充搜索)            |  ║      │     ║
║  │  ║  |                                                     |  ║      │     ║
║  │  ║  | 输出 / Writes:                                      |  ║      │     ║
║  │  ║  |   rounds/round_N/pro_turn.json <- DebateTurn schema |  ║      │     ║
║  │  ║  |   含: arguments[] (每个带 5 要素 reasoning_chain)    |  ║      │     ║
║  │  ║  |       rebuttals[] (反驳对手)                         |  ║      │     ║
║  │  ║  |       mandatory_responses[] (回应 Judge 要求)        |  ║      │     ║
║  │  ║  |       historical_wisdom (weight: advisory)           |  ║      │     ║
║  │  ║  |       speculative_scenarios (weight: exploratory)    |  ║      │     ║
║  │  ║  └─────────────────────────────────────────────────────┘  ║      │     ║
║  │  ║                                                           ║      │     ║
║  │  ║  -> validate-json.sh pro_turn.json pro_turn              ║      │     ║
║  │  ║  -> 失败: 重试最多 2 次                                   ║      │     ║
║  │  ║                                                           ║      │     ║
║  │  ║  -- 2b. CON-DEBATER ──────────────────────────────────   ║      │     ║
║  │  ║  | agent: con-debater.md                               |  ║      │     ║
║  │  ║  | model: sonnet | tools: WebSearch,WebFetch,Read,     |  ║      │     ║
║  │  ║  |        Write,Bash                                   |  ║      │     ║
║  │  ║  | 角色: 严格反对正方                                    |  ║      │     ║
║  │  ║  |                                                     |  ║      │     ║
║  │  ║  | 输入 / Reads:                                       |  ║      │     ║
║  │  ║  |   [Y] evidence_store.json                           |  ║      │     ║
║  │  ║  |   [Y] claim_ledger.json                             |  ║      │     ║
║  │  ║  |   [Y] rounds/round_N/pro_turn.json <- 本轮正方!!    |  ║      │     ║
║  │  ║  |   [Y] [round>1] round_N-1/judge_ruling.json         |  ║      │     ║
║  │  ║  |   [X] 不能读: 本轮 judge_ruling (还没写)             |  ║      │     ║
║  │  ║  |                                                     |  ║      │     ║
║  │  ║  | 关键差异 vs Pro:                                     |  ║      │     ║
║  │  ║  |   Con 能读本轮 Pro 的论点 -> 可以直接反驳             |  ║      │     ║
║  │  ║  |   Pro 不能读本轮 Con -> 只能反驳上轮                  |  ║      │     ║
║  │  ║  |   (这是 先手劣势 / 后手优势 的设计)                   |  ║      │     ║
║  │  ║  |                                                     |  ║      │     ║
║  │  ║  | 输出 / Writes:                                      |  ║      │     ║
║  │  ║  |   rounds/round_N/con_turn.json <- DebateTurn schema |  ║      │     ║
║  │  ║  └─────────────────────────────────────────────────────┘  ║      │     ║
║  │  ║                                                           ║      │     ║
║  │  ║  -> validate-json.sh con_turn.json con_turn              ║      │     ║
║  │  ║                                                           ║      │     ║
║  │  ║  -- 2c. NEUTRAL-JUDGE ────────────────────────────────   ║      │     ║
║  │  ║  | agent: neutral-judge.md                             |  ║      │     ║
║  │  ║  | model: sonnet | tools: WebSearch,WebFetch,Read,     |  ║      │     ║
║  │  ║  |        Write,Bash,Grep                              |  ║      │     ║
║  │  ║  | 角色: 独立第三方裁判                                  |  ║      │     ║
║  │  ║  |                                                     |  ║      │     ║
║  │  ║  | 输入 / Reads:                                       |  ║      │     ║
║  │  ║  |   [Y] rounds/round_N/pro_turn.json (正方本轮)       |  ║      │     ║
║  │  ║  |   [Y] rounds/round_N/con_turn.json (反方本轮)       |  ║      │     ║
║  │  ║  |   [Y] evidence_store.json (全部证据)                |  ║      │     ║
║  │  ║  |   [Y] claim_ledger.json (声明状态)                  |  ║      │     ║
║  │  ║  |                                                     |  ║      │     ║
║  │  ║  | 执行 / Does:                                        |  ║      │     ║
║  │  ║  |   * evidence-verify: 独立 WebSearch 重新验证声明    |  ║      │     ║
║  │  ║  |     (不信任辩手的引用 -> 自己搜!)                     |  ║      │     ║
║  │  ║  |   * freshness-check: 重新检查证据时效               |  ║      │     ║
║  │  ║  |   * analogy-safeguard: 验证类比结构合规             |  ║      │     ║
║  │  ║  |   * LLM: 因果链审计 (correlation != causation)      |  ║      │     ║
║  │  ║  |   * LLM: 历史智慧质量评估                            |  ║      │     ║
║  │  ║  |                                                     |  ║      │     ║
║  │  ║  | 输出 / Writes:                                      |  ║      │     ║
║  │  ║  |   rounds/round_N/judge_ruling.json <- JudgeRuling   |  ║      │     ║
║  │  ║  |   含: verification_results[]                        |  ║      │     ║
║  │  ║  |         -> 每个 claim 的 new_status                 |  ║      │     ║
║  │  ║  |       causal_validity_flags[]                       |  ║      │     ║
║  │  ║  |         -> 因果谬误标记 (severity)                  |  ║      │     ║
║  │  ║  |       mandatory_response_points[]                   |  ║      │     ║
║  │  ║  |         -> 下轮必须回应的问题 (target: pro/con/both)|  ║      │     ║
║  │  ║  |       historical_wisdom_assessment[]                |  ║      │     ║
║  │  ║  |         -> 历史类比质量评级                           |  ║      │     ║
║  │  ║  |       round_summary                                 |  ║      │     ║
║  │  ║  └─────────────────────────────────────────────────────┘  ║      │     ║
║  │  ║                                                           ║      │     ║
║  │  ║  -- 2d. POST-ROUND (Orchestrator 自己做) ──────────────  ║      │     ║
║  │  ║  |                                                     |  ║      │     ║
║  │  ║  | claim-ledger-update skill:                          |  ║      │     ║
║  │  ║  |   输入: pro_turn + con_turn -> 提取新 claims        |  ║      │     ║
║  │  ║  |   输入: judge_ruling -> verification_results        |  ║      │     ║
║  │  ║  |   输出: claim_ledger.json 更新                      |  ║      │     ║
║  │  ║  |         claim status 状态机转换:                    |  ║      │     ║
║  │  ║  |         unverified -> verified | contested | stale  |  ║      │     ║
║  │  ║  |                                                     |  ║      │     ║
║  │  ║  | append-audit.sh:                                    |  ║      │     ║
║  │  ║  |   -> audit_trail.jsonl += round_complete entry      |  ║      │     ║
║  │  ║  |                                                     |  ║      │     ║
║  │  ║  | config.json:                                        |  ║      │     ║
║  │  ║  |   -> current_round = N, status = "round_N_complete" |  ║      │     ║
║  │  ║  └─────────────────────────────────────────────────────┘  ║      │     ║
║  │  ╚═══════════════════════════════════════════════════════════╝      │     ║
║  │       ^                                                             │     ║
║  │       └──── 重复 N 轮 / Repeat for N rounds ────────────────┘      │     ║
║  └─────────────────────────────────────────────────────────────────────┘     ║
║                                                                              ║
║                                                                              ║
║  ┌─────────────────────────────────────────────────────────────────────┐     ║
║  │ PHASE 3: 最终综合 / Final Synthesis                                 │     ║
║  │                                                                     │     ║
║  │  技能: final-synthesis skill                                        │     ║
║  │  参考: references/report-templates.md (模板)                         │     ║
║  │                                                                     │     ║
║  │  输入 / Reads (汇聚全部状态):                                        │     ║
║  │    [Y] ALL rounds/round_*/pro_turn.json (全部正方论点)               │     ║
║  │    [Y] ALL rounds/round_*/con_turn.json (全部反方论点)               │     ║
║  │    [Y] ALL rounds/round_*/judge_ruling.json (全部裁定)               │     ║
║  │    [Y] evidence_store.json (全部证据 + 时效状态)                     │     ║
║  │    [Y] claim_ledger.json (全部声明 + 最终状态)                       │     ║
║  │    [Y] config.json (配置: mode, output_format, speculation_level)   │     ║
║  │                                                                     │     ║
║  │  执行 / Does:                                                       │     ║
║  │    * LLM: 分类 -> verified_facts, probable_conclusions,             │     ║
║  │           contested_points, to_verify                               │     ║
║  │    * LLM: 结论画像 (10 维度 ConclusionProfile)                     │     ║
║  │    * LLM: 场景展望 (base_case + triggers)                          │     ║
║  │    * LLM: 24h 监控清单                                              │     ║
║  │    * LLM: 执行摘要 / 决策矩阵 (按 output_format)                    │     ║
║  │    * LLM: 红队评估 (if mode=red_team)                               │     ║
║  │    * LLM: 生成双语 Markdown 报告 (EN first, CN appended)           │     ║
║  │                                                                     │     ║
║  │  输出 / Writes:                                                     │     ║
║  │    reports/final_report.json <- FinalReport schema                   │     ║
║  │    含: verdict_summary          <- 一句话总判断                      │     ║
║  │        verified_facts[]         <- 跨来源确认的事实                  │     ║
║  │        probable_conclusions[]   <- 高置信度结论                      │     ║
║  │        contested_points[]       <- 争议点 (含 pro/con position)      │     ║
║  │        to_verify[]              <- 待验证项                          │     ║
║  │        scenario_outlook{}       <- 场景展望 + 触发条件                │     ║
║  │        watchlist_24h[]          <- 24h 监控清单                      │     ║
║  │        evidence_diversity{}     <- 来源多样性评估                    │     ║
║  │        speculative_frontier[]   <- 推演前沿                          │     ║
║  │        historical_insights{}    <- 历史洞察                          │     ║
║  │        conclusion_profiles[]    <- 10 维结论画像                     │     ║
║  │        executive_summary{}      <- 执行摘要                          │     ║
║  │        decision_matrix{}        <- 决策矩阵                          │     ║
║  │                                                                     │     ║
║  │    reports/debate_report.md <- 双语 Markdown 报告                    │     ║
║  │                                                                     │     ║
║  │  -> validate-json.sh final_report.json final_report                 │     ║
║  │  -> config.json: status = "complete"                                │     ║
║  │  -> audit_trail.jsonl: action = "report_generated"                  │     ║
║  └─────────────────────────────────────────────────────────────────────┘     ║
║                                                                              ║
║                                                                              ║
║  ┌─────────────────────────────────────────────────────────────────────┐     ║
║  │ PHASE 4: 定时刷新 / Scheduled Refresh (可选)                        │     ║
║  │                                                                     │     ║
║  │  如用户同意:                                                         │     ║
║  │  -> mcp__scheduled-tasks__create_scheduled_task                      │     ║
║  │    cronExpression: "0 */6 * * *" (每 6 小时)                         │     ║
║  │    执行: SourceIngest + FreshnessCheck + EvidenceVerify              │     ║
║  │    如果证据状态变化 -> 重新生成报告                                    │     ║
║  └─────────────────────────────────────────────────────────────────────┘     ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

---

## 3. 信息流向图 / Data Flow

```
                    ┌─────────────┐
                    │ config.json │ <- 全局配置，所有 agent 可读
                    └──────┬──────┘
                           │
    ┌──────────────────────┼──────────────────────┐
    │                      │                      │
    ▼                      ▼                      ▼
┌────────────┐    ┌──────────────┐    ┌────────────────┐
│ evidence   │    │ claim        │    │ rounds/        │
│ _store.json│    │ _ledger.json │    │ round_N/       │
│            │    │              │    │ ├── pro_turn    │
│EvidenceItem│    │ ClaimItem[]  │    │ ├── con_turn    │
│    []      │    │              │    │ └── judge_ruling│
└──┬───┬───┬─┘    └──┬───┬───┬──┘    └──┬───┬───┬─────┘
   │   │   │         │   │   │          │   │   │
   R   R   R         R   R   RW         W   W   W
   │   │   │         │   │   │          │   │   │
   ▼   ▼   ▼         ▼   ▼   ▼          ▼   ▼   ▼
 Pro  Con Judge     Pro  Con  Orch     Pro  Con Judge
```

---

## 4. 读写权限矩阵 / Read-Write Access Matrix

```
                    evidence  claim    pro     con     judge    config  audit
                    _store    _ledger  _turn   _turn   _ruling
─────────────────────────────────────────────────────────────────────────────
Pro-debater         R         R        W       R(N-1)  R(N-1)   R       -
Con-debater         R         R        R(N)    W       R(N-1)   R       -
Neutral-judge       R         R        R(N)    R(N)    W        R       -
Orchestrator        RW        RW       R       R       R        RW      W
─────────────────────────────────────────────────────────────────────────────

R = Read, W = Write, RW = Read+Write
R(N) = 读本轮, R(N-1) = 读上轮
```

### 信息不对称设计 / Information Asymmetry Design

```
Round N 的信息可见性:

Pro 先手:
  能看: evidence_store + claim_ledger + [round N-1] con_turn + judge_ruling
  不能看: 本轮 con_turn (还没写)
  → Pro 只能反驳上轮的 Con

Con 后手:
  能看: 上面全部 + 本轮 pro_turn
  → Con 可以直接反驳本轮 Pro 的论点 (后手优势)

Judge 最后:
  能看: 全部 (pro_turn + con_turn + evidence + claims)
  额外能力: 独立 WebSearch (不信任任何辩手引用)
  → Judge 是唯一有独立验证能力的 agent
```

---

## 5. Skill 使用分布图 / Skill Usage Map

```
PHASE 1 (Orchestrator 直接调用)
  ├── source-ingest ──── 证据搜集 + 归一化
  └── freshness-check ── 时效标注

PHASE 2 (通过 SubAgent 间接调用)
  ├── Pro/Con SubAgent 内部:
  │   ├── debate-turn ─────── 构建论点 + 推理链
  │   ├── analogy-safeguard ─ 验证类比合规性
  │   └── evidence-verify ─── 补充搜索新证据 (可选)
  │
  ├── Judge SubAgent 内部:
  │   ├── judge-audit ──────── 独立验证 + 因果审计
  │   ├── evidence-verify ──── 独立 WebSearch 重新验证
  │   ├── freshness-check ──── 重检证据时效
  │   └── analogy-safeguard ── 验证类比结构
  │
  └── Orchestrator 回合后:
      └── claim-ledger-update ─ 状态机转换

PHASE 3 (Orchestrator 直接调用)
  └── final-synthesis ─── 汇总报告 + 结论画像
      └── references/report-templates.md (模板)
```

---

## 6. Claim 状态机 / Claim State Machine

```
                  ┌──────────┐
                  │unverified│
                  └────┬─────┘
                       │
            ┌──────────┼──────────┐
            ▼          ▼          ▼
       ┌────────┐ ┌─────────┐ ┌─────┐
       │verified│ │contested│ │stale│
       └───┬────┘ └────┬────┘ └──┬──┘
           │           │         │
           ├──>contested<────────┤
           │           │         │
           ├──>stale   │         │
           │           ├──>verified
           │           ├──>stale
           └───────────┘

转换由 Judge ruling 的 verification_results 驱动。
Reasoning-track claims 永不自动转为 stale。
```

---

## 7. Workspace 目录结构 / Workspace Directory

```
debates/<topic-slug>-<timestamp>/
├── config.json                        <- DebateConfig
├── evidence/
│   └── evidence_store.json            <- EvidenceItem[]
├── claims/
│   └── claim_ledger.json              <- ClaimItem[]
├── rounds/
│   ├── round_1/
│   │   ├── pro_turn.json              <- DebateTurn (pro)
│   │   ├── con_turn.json              <- DebateTurn (con)
│   │   └── judge_ruling.json          <- JudgeRuling
│   ├── round_2/
│   │   └── ...
│   └── round_N/
│       └── ...
├── reports/
│   ├── final_report.json              <- FinalReport
│   ├── debate_report.md               <- 双语 Markdown
│   ├── executive_summary.json         <- (if output=executive_summary)
│   └── decision_matrix.json           <- (if output=decision_matrix)
└── logs/
    └── audit_trail.jsonl              <- Append-only JSONL
```

---

## 8. 设计特点总结 / Design Highlights

1. **串行对抗** — Pro -> Con -> Judge 的顺序保证了辩论的对抗性（Con 能看到 Pro 的论点再反驳）
2. **文件即消息** — 所有 agent 间通信通过 JSON 文件，不是 API 调用
3. **读写隔离** — 每个 agent 只能写自己的输出文件，读权限严格受控
4. **Judge 独立验证** — Judge 自己 WebSearch，不信任辩手引用的来源
5. **状态机驱动** — claim_ledger 的状态转换是确定性的，每轮由 Judge 裁定驱动
6. **双轨证据** — Fact track (可过期) vs Reasoning track (永不过期)
7. **可审计性** — 每一步都有 JSON 文件落盘 + audit_trail.jsonl，完整可追溯
