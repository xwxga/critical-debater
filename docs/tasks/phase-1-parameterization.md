# Phase 1: Parameterization + Domain Adaptation
# Phase 1: 参数化 + 领域适配

## Changelog / 变更日志

| 时间 / Time | 作者 / Author | 变更 / Change |
|---|---|---|
| 2026-03-10 | Claude | 初始创建 / Initial creation |

---

## Context / 背景

当前 debate skill 只接受 topic + rounds 两个参数。credibility tier 硬编码为地缘政经标准。
需要让系统支持任意领域，并通过参数控制辩论行为。

This phase is the foundation for all subsequent upgrades. All other phases depend on `domain` and `config` fields added here.

---

## Task 1: Extend config.json Schema in Data Contracts
## 任务 1：扩展 data-contracts.md 中的 config.json Schema

**File:** `.claude/skills/source-ingest/references/data-contracts.md`

**Action:** Add a new `## DebateConfig` section after the existing `## Audit Trail Entry` section.

Add this schema definition:

```json
{
  "topic": "The debate topic",
  "rounds": 3,
  "domain": "geopolitics | tech | health | finance | philosophy | culture | general",
  "depth": "quick | standard | deep",
  "evidence_scope": "web_only | academic_included | user_provided | mixed",
  "output_format": "full_report | executive_summary | decision_matrix",
  "speculation_level": "conservative | moderate | exploratory",
  "language": "en | zh | bilingual",
  "focus_areas": ["user-defined dimensions to focus on"],
  "mode": "balanced | red_team | pre_mortem",
  "status": "initialized | in_progress | complete"
}
```

Add documentation for each field (bilingual). Include:
- `domain` defaults to `"general"` if not provided. When `"general"`, LLM infers the most appropriate domain from the topic.
- `depth` controls: number of search queries (quick=3, standard=5, deep=8), argument count per turn (quick=2, standard=2-4, deep=3-5), and evidence verification thoroughness.
- `speculation_level` controls whether `speculative_scenarios` section is generated in DebateTurn (Phase 3 dependency — for now just define the field).
- `mode` controls debate structure (Phase 4 dependency — for now just define the field).

---

## Task 2: Add Domain-Aware Credibility Guidance to SourceIngest
## 任务 2：在 SourceIngest 中添加领域感知可信度指导

**File:** `.claude/skills/source-ingest/SKILL.md`

**Action:** Modify the existing credibility tier assignment in Step 3 (Normalization).

Replace the current hardcoded tier examples with domain-aware LLM guidance. Add after the existing tier definitions:

```markdown
### Domain-Aware Credibility (v3) / 领域感知可信度

When assigning `credibility_tier`, read `config.json` for the `domain` field and apply domain-appropriate judgment:

**Guiding principle / 指导原则:** Tier reflects authority IN THE RELEVANT DOMAIN, not generic media reputation.
用领域内的权威性判断 tier，而不是通用的媒体声誉。

| Domain | tier1 guidance | tier2 guidance |
|---|---|---|
| geopolitics | Government statements, AP/Reuters, UN reports | Major newspapers, think tanks (RAND, Brookings, IISS) |
| tech | Official documentation, RFCs, IEEE/ACM | Reputable tech blogs (with deep analysis), conference papers |
| health | WHO, CDC, NIH, Lancet/NEJM/BMJ | Medical school research, clinical trial databases, Cochrane |
| finance | Central banks, SEC filings, Bloomberg/Reuters data | Research reports, industry analysis, audited financials |
| philosophy | Primary texts, Stanford Encyclopedia of Philosophy | Academic journals, established scholars' published works |
| culture | Primary sources, official archives | Academic publications, established cultural institutions |
| general | Falls back to current default tiers | Falls back to current default tiers |

**Critical rule / 关键规则:** This table is GUIDANCE for LLM judgment, NOT a lookup table to hardcode. The LLM should use semantic understanding of the source's authority within the domain context.
这个表是给 LLM 判断的指导，不是硬编码查找表。LLM 应该用语义理解来判断来源在该领域的权威性。
```

Also add to Step 1 (Keyword Generation):
```markdown
Read `domain` from config.json to adapt search query strategy:
- For `tech`: include queries targeting official docs, GitHub issues, technical benchmarks
- For `health`: include queries targeting clinical evidence, systematic reviews
- For `finance`: include queries targeting financial data, regulatory filings
- For general/geopolitics: current behavior (no change needed)
```

---

## Task 3: Update Debate Skill to Accept Parameters
## 任务 3：更新 Debate Skill 接受参数

**File:** `.claude/skills/debate/SKILL.md`

**Action:** Expand the Arguments section to support new parameters.

Replace the current argument parsing with:

```markdown
## Arguments / 参数

The user invoked this command with: $ARGUMENTS

Parse the arguments:
- **First argument**: debate topic (required, quoted string) / 辩论话题（必需）
- **Remaining arguments**: optional flags in any order / 可选标志，顺序不限

Supported flags:
- `--domain <value>`: geopolitics | tech | health | finance | philosophy | culture | general (default: auto-infer from topic)
- `--depth <value>`: quick | standard | deep (default: standard)
- `--rounds <N>`: number of rounds (default: 3)
- `--mode <value>`: balanced | red_team | pre_mortem (default: balanced)
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
```

Update the orchestrator launch prompt to include all config fields:

```markdown
1. Use the Agent tool to spawn a `debate-orchestrator` subagent with this prompt:

Run a full multi-agent debate.

Topic: <parsed topic>
Rounds: <parsed rounds>
Config: <all parsed config fields as JSON>
Project root: <current working directory>

Write the full config to debate-workspace/config.json before proceeding.
...
```

---

## Task 4: Update init-workspace.sh to Support New Config
## 任务 4：更新 init-workspace.sh 支持新配置

**File:** `scripts/init-workspace.sh`

**Action:** The script currently creates config.json with topic, rounds, and status. Update it to also accept and write the new fields. If fields are not provided, use defaults.

The orchestrator should write the full config.json after the script creates the workspace structure. The script only needs to create the directory structure — config population is the orchestrator's responsibility (LLM task, not script task).

No change needed to the script if the orchestrator handles config writing. Just verify the script doesn't overwrite config.json if it already exists.

---

## Verification / 验证

After completing all tasks:

1. Read the updated `data-contracts.md` and verify the DebateConfig schema is complete
2. Read the updated `source-ingest/SKILL.md` and verify domain-aware credibility guidance is present
3. Read the updated `debate/SKILL.md` and verify parameter parsing supports all new flags
4. Run a test: `/debate "Rust vs Go for backend services" --domain tech --depth standard`
   - Verify config.json is created with `domain: "tech"`
   - Verify SourceIngest uses tech-appropriate credibility tiers (official docs = tier1, tech blogs = tier2)
