# Phase 3: Format Breakthrough — Historical Wisdom + Speculative Scenarios
# Phase 3: 形式突破 — 历史智慧 + 想象力展开

## Changelog / 变更日志

| 时间 / Time | 作者 / Author | 变更 / Change |
|---|---|---|
| 2026-03-10 | Claude | 初始创建 / Initial creation |

---

## Context / 背景

当前系统所有论证挤在同一个 `arguments[]` 里。历史类比被 AnalogySafeguard 严格约束（≥2 similarities, <15% content share），无法从容展开历史案例。缺少想象力/推演空间。

This phase adds two new sections to DebateTurn: `historical_wisdom` (advisory weight) and `speculative_scenarios` (exploratory weight), giving debates a richer intellectual dimension beyond strict evidence-based arguments.

Depends on Phase 1 (`speculation_level` config field).

---

## Task 1: Extend DebateTurn Schema with New Sections
## 任务 1：扩展 DebateTurn Schema 增加新 Section

**File:** `.claude/skills/source-ingest/references/data-contracts.md`

**Action:** Update the DebateTurn schema to include `historical_wisdom` and `speculative_scenarios`:

```json
{
  "round": 1,
  "side": "pro | con",
  "arguments": [...],
  "rebuttals": [...],
  "mandatory_responses": [...],
  "new_evidence": [],
  "historical_wisdom": {
    "weight": "advisory",
    "references": [
      {
        "historical_event": "Name/description of historical event",
        "era_context": "Historical context and background",
        "parallel_to_current": "How this parallels the current debate topic",
        "key_differences": "Critical structural differences from current situation",
        "lesson_extracted": "The insight or lesson drawn",
        "applicability_caveat": "Limitations of this historical reference"
      }
    ]
  },
  "speculative_scenarios": {
    "weight": "exploratory",
    "scenarios": [
      {
        "scenario_name": "Short descriptive name",
        "premise": "The 'what if' starting condition",
        "chain_of_events": "A → B → C sequence of consequences",
        "probability_estimate": "low (<10%) | medium (10-40%) | high (>40%)",
        "impact_if_realized": "Severity and scope of impact",
        "early_warning_signals": ["Observable precursors to watch for"],
        "what_would_falsify": "What would invalidate this scenario"
      }
    ]
  }
}
```

Add documentation (bilingual):

```markdown
### Historical Wisdom (v3) / 历史智慧

Advisory section for historical references and lessons. NOT subject to verified/contested status determination.
建议性板块，用于历史引用和教训。不受 verified/contested 状态判定约束。

- `weight: "advisory"` — This content informs analysis but is not treated as factual evidence
- Each reference MUST include `key_differences` and `applicability_caveat` (intellectual honesty requirement)
- Unlike analogies in `arguments[]`, historical_wisdom references are not constrained by the <15% content share rule
- 与 arguments[] 中的类比不同，historical_wisdom 不受 <15% 内容占比规则的约束

### Speculative Scenarios (v3) / 推演场景

Exploratory section for imaginative scenario planning. Controlled by `config.speculation_level`.
探索性板块，用于想象力场景规划。受 `config.speculation_level` 控制。

- `weight: "exploratory"` — These are thought experiments, not predictions
- `conservative` config → this section is OMITTED entirely
- `moderate` config → generate 1-2 evidence-grounded scenarios
- `exploratory` config → generate 2-4 scenarios including black swans and non-linear paths
- Every scenario MUST include `what_would_falsify` (falsifiability requirement carries over from v2)
```

---

## Task 2: Update DebateTurn Skill to Generate New Sections
## 任务 2：更新 DebateTurn Skill 生成新 Section

**File:** `.claude/skills/debate-turn/SKILL.md`

**Action:** Add two new steps after Step 6 (Analogy Self-Check):

```markdown
### Step 7: Historical Wisdom (v3) / 历史智慧

Read `config.json` to check `domain` and topic context.

Generate 1-3 historical references relevant to the debate topic:

1. **Select historical events** that share structural similarities with the current topic
   - Prioritize events from the same domain (e.g., tech debates → historical tech transitions)
   - Cross-domain historical parallels are welcome when structurally relevant
2. **For each reference, complete ALL fields** (no partial entries):
   - `historical_event`: Clear identification of the historical case
   - `era_context`: Sufficient background for readers unfamiliar with the history
   - `parallel_to_current`: Specific, causal parallels (not superficial similarity)
   - `key_differences`: Honest acknowledgment of where the parallel breaks down
   - `lesson_extracted`: The actionable insight, not just "history repeats"
   - `applicability_caveat`: Why this lesson might not apply here
3. **Quality over quantity**: 1 deeply analyzed historical reference > 3 shallow mentions
4. This section is `weight: "advisory"` — use it to add depth, not to substitute for evidence-based arguments

**What this section is NOT / 这个板块不是:**
- NOT a replacement for evidence-based arguments (those go in `arguments[]`)
- NOT subject to the strict AnalogySafeguard rules (but still requires `key_differences`)
- NOT a place for unsupported speculation (that goes in `speculative_scenarios`)

### Step 8: Speculative Scenarios (v3) / 推演场景

Read `config.json` for `speculation_level`:
- If `conservative`: SKIP this step entirely. Set `speculative_scenarios` to `null` in output.
- If `moderate`: Generate 1-2 scenarios grounded in existing evidence
- If `exploratory`: Generate 2-4 scenarios including unconventional/black swan paths

For each scenario:
1. **Start with a clear premise**: "If X happens..." — the premise should be specific, not vague
2. **Build a chain of events**: Show the causal sequence (A leads to B leads to C)
3. **Estimate probability honestly**: Use the three-tier system (low/medium/high)
4. **Assess impact**: What would happen if this scenario materializes?
5. **Identify early warning signals**: What observable events would precede this scenario?
6. **Include falsification**: What would prove this scenario impossible?

**Guidelines / 指导原则:**
- `moderate` scenarios should be plausible extensions of verified facts
- `exploratory` scenarios can include:
  - Black swan events (low probability, high impact)
  - Non-linear cascading effects
  - Scenarios that challenge conventional wisdom
  - "What if the opposite happens?" inversions
- Even `exploratory` scenarios must have an internally consistent causal chain
- Avoid pure fantasy — every scenario should be at least theoretically possible
```

---

## Task 3: Update AnalogySafeguard for Dual Mode
## 任务 3：更新 AnalogySafeguard 支持双模式

**File:** `.claude/skills/analogy-safeguard/SKILL.md`

**Action:** Add a mode parameter to distinguish between strict and advisory contexts:

```markdown
## Input / 输入 (v3 update)

- `content`: The debate turn content to validate
- `mode`: "strict" | "advisory" (default: "strict")
  - `strict`: Used for analogies in `arguments[]` — full rules apply (≥2 similarities, ≥1 difference, <15% content share)
  - `advisory`: Used for `historical_wisdom` section — relaxed rules (requires `key_differences` and `applicability_caveat`, but no content share limit)

## Workflow Update / 工作流更新

### For `mode = "strict"` (arguments[]):
Current behavior unchanged:
1. ≥2 similarities (causally relevant, not superficial)
2. ≥1 key structural difference
3. Content share <15% (LLM semantic judgment)
4. Failed analogies → "heuristic only"

### For `mode = "advisory"` (historical_wisdom):
1. Verify `key_differences` field is substantive (not a token acknowledgment)
2. Verify `applicability_caveat` field is present and meaningful
3. NO content share limit — historical references can be explored in depth
4. Grade quality: "strong_parallel" | "moderate_parallel" | "weak_parallel"
5. If `weak_parallel`: suggest in output that the reference may not add value
```

---

## Task 4: Update JudgeAudit for New Sections
## 任务 4：更新 JudgeAudit 处理新 Section

**File:** `.claude/skills/judge-audit/SKILL.md`

**Action:** Add a new step after Step 3 (Analogy Audit):

```markdown
### Step 3.5: Historical Wisdom Assessment (v3) / 历史智慧评估

For each `historical_wisdom` reference from both sides:

1. **Structural relevance check**: Does the historical case genuinely parallel the current topic, or is it a superficial connection?
2. **Difference honesty check**: Are the `key_differences` genuinely acknowledged, or minimized to make the parallel seem stronger?
3. **Lesson validity check**: Does the extracted lesson logically follow from the historical case?
4. **Cross-side comparison**: If both sides cite conflicting historical lessons, note the tension

Produce `historical_wisdom_assessment` in JudgeRuling:
```json
{
  "historical_wisdom_assessment": [
    {
      "side": "pro | con",
      "historical_event": "...",
      "relevance_grade": "strong_parallel | moderate_parallel | weak_parallel",
      "honesty_grade": "honest | partially_honest | misleading",
      "note": "..."
    }
  ]
}
```

**Key principle / 关键原则:** Judge evaluates the QUALITY of historical reasoning, not whether the historical lesson supports pro or con. A well-analyzed weak parallel is better than a poorly analyzed strong one.
Judge 评估历史推理的质量，而非历史教训支持正方还是反方。

### Step 3.6: Speculative Scenarios Review (v3) / 推演场景审查

For each `speculative_scenario` from both sides:

1. **Internal consistency**: Does the chain of events make causal sense?
2. **Probability calibration**: Is the probability estimate reasonable given the premise?
3. **Falsifiability**: Is `what_would_falsify` genuinely testable?
4. **Novelty**: Does this scenario add new insight, or just restate existing arguments as "what if"?

Do NOT verify or score speculative scenarios — they are by definition unverifiable. Instead, note quality of reasoning.
不要验证或评分推演场景 — 它们本质上不可验证。仅评估推理质量。
```

Update the JudgeRuling schema in data-contracts.md to include `historical_wisdom_assessment`.

---

## Task 5: Update FinalSynthesis to Integrate New Sections
## 任务 5：更新 FinalSynthesis 整合新 Section

**File:** `.claude/skills/final-synthesis/SKILL.md`

**Action:** Add a new step after Step 3 (Scenario Outlook):

```markdown
### Step 3.5: Speculative Frontier (v3) / 推演前沿

If `config.speculation_level` is not `conservative`:

1. Collect all `speculative_scenarios` from both sides across all rounds
2. Deduplicate scenarios that explore similar premises
3. Sort by: impact_if_realized (highest first), then probability_estimate
4. For each scenario, note which side proposed it and the Judge's quality assessment
5. Present as a separate section — clearly labeled as exploratory, not conclusive

Include in FinalReport:
```json
{
  "speculative_frontier": [
    {
      "scenario_name": "...",
      "proposed_by": "pro | con",
      "premise": "...",
      "chain_of_events": "...",
      "probability": "...",
      "impact": "...",
      "early_warnings": ["..."],
      "judge_quality_note": "..."
    }
  ]
}
```

### Step 3.6: Historical Wisdom Summary (v3) / 历史智慧汇总

Collect all `historical_wisdom` references from both sides:

1. Identify the most impactful historical parallels (based on Judge's relevance_grade)
2. Note conflicting historical lessons between sides
3. Extract overarching historical patterns that emerged

Include in FinalReport:
```json
{
  "historical_insights": {
    "key_parallels": ["Most relevant historical parallels and their lessons..."],
    "conflicting_lessons": ["Where historical evidence points in different directions..."],
    "meta_pattern": "Overarching historical pattern, if any..."
  }
}
```

Update the FinalReport schema in data-contracts.md to include `speculative_frontier` and `historical_insights`.

---

## Verification / 验证

After completing all tasks:

1. Read all modified files and verify schema consistency across data-contracts.md and all skill files
2. Run a test debate with `--speculation exploratory` on a topic with rich historical context
   - Example: `/debate "Will AI cause mass unemployment?" --speculation exploratory`
   - Verify DebateTurn output includes `historical_wisdom` and `speculative_scenarios` sections
   - Verify Judge produces `historical_wisdom_assessment`
   - Verify FinalReport includes `speculative_frontier` and `historical_insights`
3. Run a test debate with `--speculation conservative`
   - Verify `speculative_scenarios` is omitted from DebateTurn
   - Verify FinalReport has no `speculative_frontier` section
4. Verify AnalogySafeguard dual mode:
   - Analogies in `arguments[]` still enforce strict rules
   - Historical references in `historical_wisdom` allow deeper exploration
