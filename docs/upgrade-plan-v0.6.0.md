# Skill Upgrade v0.6.0 — Agent Skills Open Standard + skills.sh
# Skill 升级 v0.6.0 — Agent Skills 开放标准 + skills.sh 兼容

## Changelog / 变更日志

| 时间 / Time | 作者 / Author | 变更 / Change |
|---|---|---|
| 2026-03-11 | Claude | 初始创建 / Initial creation |

---

## Context / 背景

Critical Debater 的 9 个 skill 需要发布到 [skills.sh](https://skills.sh)（Vercel 推出的 Agent Skills 包管理器，支持 18+ AI agent 平台）。当前 v0.5.0 skill 功能完整但：

1. **Frontmatter 结构不合规** — `version` 在顶层（spec 没有此字段），`metadata.openclaw` 非标准
2. **Description 混中文** — 影响 skills.sh 跨平台搜索索引（Cursor, Codex, Copilot 等）
3. **缺少 evals** — 没有评测用例，无法量化 skill 质量
4. **final-synthesis 过长** — 402 行，超过 spec 建议的 <500 行

**目标**: v0.5.0 → v0.6.0，完全符合 [Agent Skills Specification](https://agentskills.io/specification)，可发布 skills.sh。

**参考标准**:
- Agent Skills Specification: https://agentskills.io/specification
- Anthropic skill-creator: https://github.com/anthropics/skills/tree/main/skills/skill-creator
- skills.sh: https://skills.sh

---

## 变更概览 / Change Overview

| # | 类别 | 变更 | 影响文件数 |
|---|---|---|---|
| 1 | Frontmatter 标准化 | `version` 移入 `metadata`，移除 `openclaw` wrapper，加 `compatibility` | 9 SKILL.md |
| 2 | Description 优化 | 全英文、trigger-heavy、"pushy" 风格，中文仅保留在 body | 9 SKILL.md |
| 3 | final-synthesis 瘦身 | 提取报告模板到 `references/`，body 从 383→~250 行 | 1 SKILL.md + 1 新文件 |
| 4 | Evals 评测 | 每个 skill 创建 `evals/evals.json`（10-12 条） | 9 新文件 |
| 5 | Version bump | 全部升到 v0.6.0 + changelog | 9 SKILL.md |
| 6 | 文档更新 | CLAUDE.md、README.md 更新版本和说明 | 2 文件 |

**总变更**: 9 SKILL.md 修改 + 10 新文件 + 2 文档更新

---

## 执行顺序 / Execution Order

```
Step 1 + Step 2 ──→ 同时改 frontmatter + description (9 files)
       │
       ▼
Step 3 ──→ final-synthesis 提取 references/ (创建新文件 + 修改 SKILL.md)
       │
       ▼
Step 4 ──→ 创建 9 个 evals/evals.json
       │
       ▼
Step 5 ──→ Version bump + changelog (在 Step 1-4 完成后)
       │
       ▼
Step 6 ──→ CLAUDE.md + README.md 更新
       │
       ▼
Step 7 ──→ 验证
```

---

## Step 1: Frontmatter 标准化 (9 files)

### Agent Skills Spec 合法字段

来源：[agentskills.io/specification](https://agentskills.io/specification)

| Field | Required | 当前状态 | 动作 |
|---|---|---|---|
| `name` | ✅ Required | ✅ 已有 | 不变 |
| `description` | ✅ Required | ⚠️ 混中文 | Step 2 优化 |
| `license` | Optional | ✅ MIT-0 | 不变 |
| `compatibility` | Optional | ❌ 缺失 | 新增（环境要求） |
| `metadata` | Optional | ⚠️ 有 `openclaw` 子结构 | 扁平化 |
| `allowed-tools` | Optional (实验性) | ❌ 缺失 | 暂不加（不稳定） |

**关键**: `version` 不是 spec 顶层字段 → 必须移入 `metadata.version`

### Before / After 对照

**Before** (当前 v0.5.0):
```yaml
---
name: source-ingest
description: >
  This skill should be used when... 中文描述。
version: 0.5.0
license: MIT-0
metadata:
  openclaw:
    requires:
      bins: [bash, shasum]
    homepage: "https://github.com/xwxga/critical-debater"
    emoji: "🔍"
---
```

**After** (目标 v0.6.0):
```yaml
---
name: source-ingest
description: >
  Searches, fetches, and normalizes web sources into structured EvidenceItem
  format for debate evidence stores. Use this skill when the debate system
  needs to search for evidence, gather sources, ingest and normalize sources,
  fetch web content, build the initial evidence store, or perform domain-aware
  credibility assessment with social media misinformation pre-screening.
license: MIT-0
compatibility: Requires bash and shasum. Internet access required for WebSearch and WebFetch.
metadata:
  version: "0.6.0"
  author: xwxga
  homepage: "https://github.com/xwxga/critical-debater"
  tags: debate, evidence, web-search, source-verification
  emoji: "🔍"
---
```

### 变更清单

对每个 skill 做以下操作：
1. **删除顶层 `version: 0.5.0`**
2. **替换 `metadata` 块**：移除 `openclaw.requires.bins` 嵌套，改为扁平 key-value
3. **添加 `compatibility`**（如有环境要求）
4. **添加 `metadata.author: xwxga`**
5. **添加 `metadata.tags`**（用逗号分隔的关键词）

### 每个 skill 的 `compatibility` 和 `tags` 值

| Skill | compatibility | tags |
|---|---|---|
| analogy-safeguard | _(omit)_ | `debate, analogy, historical-reasoning, validation` |
| claim-ledger-update | `Requires bash and jq for JSON validation and audit trail.` | `debate, claims, state-machine, audit-trail` |
| debate | `Requires bash, jq, python3, and shasum. Internet access for WebSearch.` | `debate, multi-agent, evidence-verification, reasoning` |
| debate-turn | `Requires bash and shasum. Internet access for evidence search.` | `debate, argument, reasoning-chain, rebuttal` |
| evidence-verify | `Internet access needed for independent source verification.` | `debate, evidence, verification, cross-source` |
| final-synthesis | `Requires bash and jq for JSON validation.` | `debate, report, synthesis, conclusion-profiles` |
| freshness-check | `Internet access needed for real-time capability check.` | `debate, evidence, freshness, timeliness` |
| judge-audit | `Requires bash and jq. Internet access for independent verification.` | `debate, judge, causal-audit, verification` |
| source-ingest | `Requires bash and shasum. Internet access for WebSearch and WebFetch.` | `debate, evidence, web-search, source-verification` |

---

## Step 2: Description 优化 (9 files)

### 原则

- **全英文** — 中文仅保留在 SKILL.md body，不放 description
- **"Pushy" 风格** — 包含尽可能多的触发短语，让 agent 更容易匹配
- **≤1024 chars** — Spec 硬限制
- **动作导向** — `Use this skill when...` + 具体触发场景

### 9 个新 Description

#### debate (入口 skill，最关键)
```yaml
description: >
  Launches a multi-agent debate on any topic with real-time evidence verification
  and causal reasoning chains. Use this skill when the user says "debate", "start
  a debate", "run a debate on", "argue about", "red team this", "analyze from
  multiple perspectives", or provides a topic for critical examination. Supports
  balanced and red-team modes, configurable depth and rounds, domain-aware evidence
  gathering, and generates structured Markdown reports with conclusion profiles
  and 24h watchlists.
```

#### source-ingest
```yaml
description: >
  Searches, fetches, and normalizes web sources into structured EvidenceItem format
  for debate evidence stores. Use this skill when the debate system needs to search
  for evidence, gather sources for a topic, ingest and normalize sources, fetch web
  content for evidence, build the initial evidence store, find supporting data for
  arguments, perform domain-aware credibility assessment, or pre-screen social media
  sources for misinformation indicators.
```

#### debate-turn
```yaml
description: >
  Constructs a complete structured debate turn with 5-element reasoning chains,
  rebuttals, and evidence references. Use this skill when a debater agent needs to
  construct an argument, build a debate turn, generate rebuttals against opponent,
  respond to mandatory judge response points, create a structured argument with
  evidence and causal reasoning chain, or produce a debate round output with
  historical wisdom and speculative scenarios.
```

#### judge-audit
```yaml
description: >
  Performs independent verification, causal chain audit, analogy validation, and
  generates structured rulings for debate rounds. Use this skill when the judge agent
  needs to audit a debate round, verify claims independently, check causal validity
  of arguments, produce a structured ruling, identify mandatory response points for
  next round, perform independent second-pass verification, evaluate reasoning quality,
  assess historical wisdom references, or review speculative scenarios.
```

#### evidence-verify
```yaml
description: >
  Performs cross-source verification, credibility validation, and independent re-search
  for debate evidence. Use this skill when the judge needs to verify evidence
  independently, cross-check sources, validate a claim's supporting evidence, check
  if Twitter-only claims have independent corroboration, perform independent source
  verification, assess evidence credibility, or determine claim verification status.
```

#### final-synthesis
```yaml
description: >
  Generates the final debate report with verified facts, probable conclusions, enriched
  contested points, scenario outlook, conclusion profiles, and 24h watchlist. Use this
  skill when the orchestrator needs to generate the final debate report, synthesize all
  rounds into conclusions, create output with watchlist and scenario outlook, produce
  the debate summary, compile verified facts and contested points, or generate bilingual
  Markdown and English JSON reports.
```

#### freshness-check
```yaml
description: >
  Validates evidence timeliness and tags freshness status based on evidence track type.
  Use this skill when the system needs to check evidence freshness, validate timeliness
  of claims, tag evidence as current or stale or timeless, verify real-time information
  capability, assess source currency, or distinguish fact-track evidence (time-sensitive)
  from reasoning-track evidence (timeless).
```

#### claim-ledger-update
```yaml
description: >
  Manages the claim state machine for a multi-agent debate system. Use this skill when
  the orchestrator needs to update the claim ledger, record new claims from a debate turn,
  change claim status based on judge ruling, track claim state transitions, extract claims
  from arguments, perform batch updates from judge rulings, or manage the claim lifecycle
  with audit trail persistence.
```

#### analogy-safeguard
```yaml
description: >
  Validates historical and classical analogies in debate arguments for structural
  compliance. Use this skill when checking if an analogy has sufficient similarities and
  differences, assessing analogy content share percentage, validating historical parallel
  structure, auditing classical reference compliance, or verifying debate arguments that
  reference historical precedents. Supports strict mode for core arguments and advisory
  mode for historical wisdom sections.
```

---

## Step 3: final-synthesis 瘦身 (1 SKILL.md + 1 new file)

### 问题

当前 402 行（body 383 行）。Spec 建议 body <500 lines / <5000 tokens。虽然没超硬限制，但提取大段模板是最佳实践。

### 操作

**创建新文件**: `.claude/skills/final-synthesis/references/report-templates.md`

从 `final-synthesis/SKILL.md` 提取以下内容到新文件：

1. **Output Format: `executive_summary`** (当前 lines 245-255) — 凝缩格式说明
2. **Output Format: `decision_matrix`** (当前 lines 257-269) — 结构化决策格式
3. **Red Team Report Format** (当前 lines 271-296) — JSON 模板 + 字段说明
4. **Step 6: Markdown Report Template** (当前 lines 298-393) — 完整 MD 模板结构（EN + CN skeleton）

**在 SKILL.md 原位替换为引用**:

```markdown
### Output Format Variants & Report Templates
### 输出格式变体和报告模板

See [references/report-templates.md](references/report-templates.md) for:
参见 [references/report-templates.md](references/report-templates.md)：

- `full_report` (default): Complete FinalReport with all sections / 完整报告
- `executive_summary`: Condensed version / 凝缩版
- `decision_matrix`: Structured decision format / 结构化决策格式
- Red Team report JSON structure / 红队报告 JSON 结构
- Complete Markdown report template (EN + CN) / 完整 Markdown 报告模板
```

**注意**: `report-templates.md` 需要自己的标题和 changelog。

**预期结果**: SKILL.md 从 402 行 → ~260 行

---

## Step 4: Evals 评测 (9 new files)

### 文件路径

每个 skill 创建：`.claude/skills/<skill-name>/evals/evals.json`

### JSON 格式

```json
{
  "skill_name": "<name-matching-frontmatter>",
  "evals": [
    {
      "id": 1,
      "prompt": "realistic user prompt that should trigger this skill",
      "should_trigger": true,
      "expected_behavior": "brief description of what the skill should do"
    },
    {
      "id": 2,
      "prompt": "similar-sounding prompt that should NOT trigger this skill",
      "should_trigger": false,
      "expected_behavior": "this is NOT a debate task, should be handled by a different tool"
    }
  ]
}
```

### 数量要求

每个 skill **10-12 条**:
- 6-7 条 `should_trigger: true`（包含正常用例 + 边界场景）
- 4-5 条 `should_trigger: false`（"近似但不该触发" — near misses，共享关键词但需要不同工具的 prompt）

### Eval 设计指南

**should_trigger: true** 应该包含：
- 直接触发短语（"debate this topic"）
- 间接触发（"what are the pros and cons of..."）
- 边界场景（"red team our migration plan"）
- 不同措辞（中文 prompt 也算，因为系统是双语的）

**should_trigger: false** 应该是 "near misses"：
- 共享关键词但语义不同（"audit my code" vs "audit the debate round"）
- 相似但不是辩论系统的任务（"summarize this article" vs "synthesize debate rounds"）

### 参考表

| Skill | should_trigger 示例 | should_NOT_trigger 示例 |
|---|---|---|
| debate | "debate whether AI will replace jobs", "red team our migration plan", "argue about remote work" | "prepare for my debate class", "what does debate mean", "compare React vs Vue" |
| source-ingest | "search for evidence on climate policy", "build evidence store for this debate", "gather sources on AI regulation" | "search my codebase for bugs", "ingest this CSV into database", "find files matching pattern" |
| debate-turn | "construct pro argument for round 2", "respond to judge's mandatory points", "build rebuttal against con" | "write a persuasive essay", "outline my presentation", "generate talking points for meeting" |
| judge-audit | "audit round 2 claims independently", "produce judge ruling", "verify both sides' evidence" | "review my pull request", "audit codebase for security", "judge which framework is better" |
| evidence-verify | "cross-check this Twitter claim", "verify evidence independently", "validate claim's sources" | "verify my code compiles", "check if JSON schema is valid", "validate form input" |
| freshness-check | "check if evidence is still current", "tag freshness status", "is this 2024 data still valid" | "check if npm package is outdated", "is this food fresh", "when was file last modified" |
| claim-ledger-update | "extract claims from pro turn", "update claim status to verified", "batch update from judge ruling" | "update the changelog", "track issue in Jira", "log this event" |
| final-synthesis | "generate final debate report", "synthesize all 3 rounds", "compile conclusions with watchlist" | "summarize this meeting", "write my paper conclusion", "generate project report" |
| analogy-safeguard | "validate analogies in debate turn", "check if 2008 crisis analogy is valid", "audit historical references" | "write an analogy to explain recursion", "give me a historical example", "compare two code patterns" |

---

## Step 5: Version Bump + Changelog (9 files)

### 操作

对所有 9 个 SKILL.md：

1. 确保 `metadata.version` 已设为 `"0.6.0"`（Step 1 已处理）
2. 在 Changelog 表格**最上方**添加新条目：

```markdown
| 2026-03-11 | Claude | v0.6.0: Agent Skills open standard compliance — frontmatter restructured, English-only description, progressive disclosure, evals added / Agent Skills 开放标准兼容 — 前置元数据重构、纯英文描述、渐进式披露、添加评测 |
```

---

## Step 6: 文档更新 (2 files)

### 6A: `.claude/CLAUDE.md`

1. **版本号**: `v0.5.0` → `v0.6.0`
2. **描述更新**: 加入 "Agent Skills open standard compliant, skills.sh compatible"
3. **Changelog 新增条目**:
```markdown
| 2026-03-11 | Claude | v0.6.0 升级：Agent Skills 开放标准兼容、描述优化、渐进式披露、evals 评测 / v0.6.0 upgrade: Agent Skills open standard compliance, description optimization, progressive disclosure, evals |
```

### 6B: `README.md`

1. **Tech Stack** 部分加入：
   - `**Skills**: 9 composable skills, [Agent Skills](https://agentskills.io) open standard compliant`
2. **Quick Start** 部分考虑加入 skills.sh 安装方式（如果 skills.sh 支持）
3. 确保版本描述一致

---

## Step 7: 验证 / Verification

### 自动检查清单

完成所有修改后，运行以下验证：

```bash
# 1. 所有 SKILL.md 存在且有 name + description
for f in .claude/skills/*/SKILL.md; do
  echo "=== $f ==="
  head -3 "$f" | grep -E "^(name|description):"
done

# 2. 没有顶层 version: 字段（应在 metadata 内）
for f in .claude/skills/*/SKILL.md; do
  # 提取 frontmatter，检查是否有顶层 version
  awk '/^---$/{n++} n==1{print}' "$f" | grep -E "^version:" && echo "FAIL: $f has top-level version"
done

# 3. name 与目录名一致
for dir in .claude/skills/*/; do
  dirname=$(basename "$dir")
  name=$(grep "^name:" "$dir/SKILL.md" | head -1 | awk '{print $2}')
  [ "$dirname" = "$name" ] || echo "FAIL: $dirname != $name"
done

# 4. description 不含中文字符
for f in .claude/skills/*/SKILL.md; do
  desc=$(awk '/^---$/{n++} n==1 && /^description:/{found=1} found && /^[a-z]/{found=0} found{print}' "$f")
  echo "$desc" | grep -P '[\x{4e00}-\x{9fff}]' && echo "FAIL: $f description contains Chinese"
done

# 5. 所有 metadata.version = "0.6.0"
for f in .claude/skills/*/SKILL.md; do
  grep -A1 'version:' "$f" | grep "0.6.0" || echo "CHECK: $f version"
done

# 6. final-synthesis body 行数
wc -l .claude/skills/final-synthesis/SKILL.md
# 应该 < 300

# 7. 所有 evals/evals.json 存在且合法
for dir in .claude/skills/*/; do
  f="$dir/evals/evals.json"
  [ -f "$f" ] || echo "MISSING: $f"
  python3 -c "import json; json.load(open('$f'))" 2>/dev/null || echo "INVALID JSON: $f"
done

# 8. 没有残留 metadata.openclaw
grep -r "openclaw" .claude/skills/*/SKILL.md && echo "FAIL: openclaw remnants found"

# 9. report-templates.md 存在
[ -f .claude/skills/final-synthesis/references/report-templates.md ] || echo "MISSING: report-templates.md"
```

### 手动验证

1. `git diff` 审查所有变更
2. 确认 SKILL.md body 内容没被意外删除（仅 frontmatter 和 final-synthesis 模板部分变动）
3. 确认 debate 系统仍能正常运行（描述变更不影响 body 指令逻辑）

---

## 关键文件路径 / Critical Files

| 文件 | 操作 |
|---|---|
| `.claude/skills/analogy-safeguard/SKILL.md` | 改 frontmatter + description + changelog |
| `.claude/skills/claim-ledger-update/SKILL.md` | 改 frontmatter + description + changelog |
| `.claude/skills/debate/SKILL.md` | 改 frontmatter + description + changelog |
| `.claude/skills/debate-turn/SKILL.md` | 改 frontmatter + description + changelog |
| `.claude/skills/evidence-verify/SKILL.md` | 改 frontmatter + description + changelog |
| `.claude/skills/final-synthesis/SKILL.md` | 改 frontmatter + description + changelog + 提取模板 |
| `.claude/skills/freshness-check/SKILL.md` | 改 frontmatter + description + changelog |
| `.claude/skills/judge-audit/SKILL.md` | 改 frontmatter + description + changelog |
| `.claude/skills/source-ingest/SKILL.md` | 改 frontmatter + description + changelog |
| `.claude/skills/final-synthesis/references/report-templates.md` | **新建** |
| `.claude/skills/*/evals/evals.json` (×9) | **新建** |
| `.claude/CLAUDE.md` | 版本 + changelog |
| `README.md` | 版本 + skills.sh 说明 |
