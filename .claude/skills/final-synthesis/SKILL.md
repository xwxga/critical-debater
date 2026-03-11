---
name: final-synthesis
description: >
  This skill should be used when the orchestrator needs to "generate the final debate report",
  "synthesize all rounds into a conclusion", "create the final output with watchlist and
  scenario outlook", "produce the debate summary", or "compile verified facts, contested
  points, and recommendations". Generates the final debate report from all rounds' data.
  从所有回合数据生成最终辩论报告，含结论画像和 Markdown 报告。
version: 0.2.0
license: MIT-0
metadata:
  openclaw:
    requires:
      bins: [bash, jq]
    homepage: "https://github.com/xwxga/insight-debator"
    emoji: "📊"
---

# FinalSynthesis
# 最终综合

Generate the final debate report with verified facts, probable conclusions, contested points, scenario outlook, and 24h watchlist.
生成包含已验证事实、可能结论、争议点、情景展望和 24h 监控清单的最终辩论报告。

## When to Use / 何时使用

- After all debate rounds are complete / 所有辩论回合完成后
- When evidence state changes during refresh trigger report regeneration / 刷新时证据状态变化触发报告重新生成
- See `references/data-contracts.md` for FinalReport output schema

## Input / 输入

- `workspace_path`: Path to the debate workspace directory
- All round data: `rounds/round_*/` (pro_turn, con_turn, judge_ruling for each round)
- `claim_ledger_path`: Path to claim_ledger.json
- `evidence_store_path`: Path to evidence_store.json
- `config_path`: Path to config.json

## Output / 输出

- `FinalReport` JSON written to `reports/final_report.json`
- Markdown report written to `reports/debate_report.md`
- Human-readable summary for the user (bilingual Chinese + English)

## Core Workflow / 核心工作流

### Step 0: Read Output Format / 读取输出格式

Read `config.json` for `output_format` field. This controls the report detail level.

### Step 1: Aggregate All Rounds / 聚合所有回合

1. Read all round data chronologically (round 1, 2, ..., N)
2. Read the final claim ledger
3. Track how each claim's status evolved across rounds:
   - Was it challenged? When was it verified?
   - Did the judge flag issues? Were they resolved?

### Step 2: Categorize Claims / 分类声明

From the final claim ledger, categorize:

**Verified Facts / 已验证事实**:
- Claims with `status = verified`
- Cross-source confirmed
- Present as factual statements with source references
- Include ONLY claims verified by the Judge's independent check

**Probable Conclusions / 高概率结论**:
- Claims with strong reasoning chains that survived all rounds
- Claims where evidence supports but doesn't fully confirm
- Present with appropriate confidence qualifiers ("likely", "evidence suggests")

**Contested Points / 争议点**:
- Claims with `status = contested`
- Include BOTH sides' strongest arguments on each contested point
- Present the strongest version of each side's case

**Items Requiring Verification / 待验证项**:
- Claims with `status = unverified`
- Include suggested verification methods (what data would resolve this?)
- Prioritize by importance to the overall debate conclusion

### Step 2.5: Generate Conclusion Profiles / 生成结论画像

For each major conclusion in `verified_facts` and `probable_conclusions`:

1. **Identify the conclusion**: Group related claims into a single conclusion statement
2. **Link source claims**: Reference the `claim_id`s that support this conclusion
3. **Evaluate each of the 10 dimensions** using LLM semantic judgment:
   - Read the claim statuses from claim_ledger
   - Read the Judge's verification results and causal validity flags
   - Read the evidence store for source quality and diversity
   - Consider the debate trajectory (did this conclusion strengthen or weaken across rounds?)
4. **Write a concise rationale** for each dimension (1-2 sentences, bilingual)

**Guidelines / 指导原则:**
- NOT every conclusion needs all 10 dimensions. Focus on the dimensions that are most informative for each specific conclusion.
  不是每个结论都需要全部 10 个维度。聚焦于对该特定结论最有信息量的维度。
- For verified facts: focus on confidence, evidence_coverage, validity_window
- For probable conclusions: focus on probability, confidence, reversibility, causal_clarity
- For contested points: focus on consensus, evidence_coverage, falsifiability
- Include the top 3-5 conclusions as full profiles; others can be light profiles (3-4 dimensions only)

### Step 3: Build Scenario Outlook / 构建情景展望

Based on verified facts and probable conclusions:

**Base case / 基准情景**:
- Most likely outcome based on the weight of evidence
- Ground it in verified facts, not speculation

**Upside triggers / 上行触发条件**:
- Specific events or data points that would improve the outlook
- Must be concrete and observable

**Downside triggers / 下行触发条件**:
- Specific events or data points that would worsen the outlook
- Must be concrete and observable

**Falsification conditions / 证伪条件**:
- What would completely invalidate the base case?
- These come from the strongest falsification conditions in the debate

### Step 3.5: Speculative Frontier / 推演前沿

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

### Step 3.6: Historical Wisdom Summary / 历史智慧汇总

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

### Step 4: Create 24h Watchlist / 创建 24h 监控清单

Items that could change conclusions if new information arrives within 24 hours:

For each watchlist item:
- `item`: What to monitor (specific data point, event, announcement)
- `reversal_trigger`: What change would reverse current conclusions
- `monitoring_source`: Where to look (specific publications, data sources, feeds)

Focus on:
- Stale claims that could be refreshed with new data
- Contested points where new evidence could tip the balance
- Trigger conditions identified in the scenario outlook

### Step 4.5: Source Diversity Assessment / 来源多样性评估

Analyze the complete evidence store to assess diversity:

1. **Source type distribution / 来源类型分布:**
   Count evidence items by `source_type` (web, twitter, academic, government, other)

2. **Credibility tier distribution / 可信度层级分布:**
   Count by `credibility_tier`. Flag if >70% of evidence is tier3/tier4.

3. **Geographic/perspective assessment / 地域/视角评估:**
   Use LLM to assess: Are sources geographically diverse? Do they represent multiple perspectives/viewpoints?
   Flag if all sources come from a single country or represent only one perspective.

4. **Diversity warning / 多样性警告:**
   Generate a warning if significant gaps exist (e.g., "Evidence heavily skewed toward US English-language media. Consider seeking sources from [relevant other perspectives].")

Include in FinalReport:
```json
{
  "evidence_diversity_assessment": {
    "source_type_distribution": {"web": 15, "academic": 3, "twitter": 8},
    "credibility_tier_distribution": {"tier1": 2, "tier2": 8, "tier3": 10, "tier4": 8},
    "geographic_diversity": "assessment text...",
    "perspective_balance": "assessment text...",
    "diversity_warning": "warning text or null"
  }
}
```

### Step 5: Write Report / 写入报告

1. Assemble into FinalReport JSON schema
2. **Bilingual content requirement / 双语内容要求**:
   ALL user-facing text fields MUST be bilingual: `中文内容 / English content`
   所有面向用户的文本字段必须双语格式。辩论 agents 的原始数据可能是英文，你需要在综合时翻译为双语。
   Affected fields / 涉及字段:
   - `verified_facts[]` (each item)
   - `probable_conclusions[]` (each item)
   - `contested_points[]` (each item)
   - `to_verify[]` (each item)
   - `verdict_summary`
   - `scenario_outlook.base_case`, `upside_triggers[]`, `downside_triggers[]`, `falsification_conditions[]`
   - `watchlist_24h[].item`, `watchlist_24h[].reversal_trigger`
   - `conclusion_profiles[].conclusion_text`, `conclusion_profiles[].profile.*.rationale`
   - `historical_insights.key_parallels[]`, `historical_insights.conflicting_lessons[]`, `historical_insights.meta_pattern`
   - `speculative_frontier[].premise`, `speculative_frontier[].chain_of_events`, `speculative_frontier[].impact`
   - `evidence_diversity_assessment.geographic_diversity`, `evidence_diversity_assessment.perspective_balance`, `evidence_diversity_assessment.diversity_warning`
3. Write to `reports/final_report.json`
4. Validate with `scripts/validate-json.sh <file> final_report`
5. Log report generation via `scripts/append-audit.sh`

#### Output Format: `full_report` (default)
Current behavior — generate complete FinalReport with all sections.

#### Output Format: `executive_summary`
Generate a condensed version:
1. One-paragraph summary of the debate conclusion (bilingual)
2. Top 3-5 verified facts (bullet points)
3. Top 2-3 contested points with one-sentence explanation each
4. Scenario outlook: base case + top 2 triggers only
5. Top 3 watchlist items

Write to `reports/executive_summary.json` AND `reports/final_report.json` (full version still generated for reference).

Present the executive summary to the user, with a note that the full report is available.

#### Output Format: `decision_matrix`
Generate a structured decision matrix:
1. Extract the core decision dimensions from the debate (LLM identifies 4-8 key factors)
2. For each dimension:
   - Factor name
   - Pro side's evidence/argument summary (1-2 sentences)
   - Con side's evidence/argument summary (1-2 sentences)
   - Evidence strength: strong | moderate | weak (based on claim statuses)
   - Judge's assessment note
3. Overall recommendation: Which side has stronger evidence across factors?
4. Key uncertainty: What single factor could flip the conclusion?

Write to `reports/decision_matrix.json` AND `reports/final_report.json`.

### Red Team Report Format / 红队报告格式

When `config.mode = "red_team"`, replace the standard FinalReport structure with:

```json
{
  "topic": "...",
  "mode": "red_team",
  "risk_assessment": [
    {
      "risk_id": "risk_1",
      "risk_description": "...",
      "severity": "critical | high | medium | low",
      "likelihood": "high | medium | low",
      "risk_score": "severity x likelihood qualitative",
      "red_team_argument": "How and why this risk could materialize...",
      "blue_team_mitigation": "Proposed mitigation and residual risk...",
      "judge_verdict": "Is mitigation feasible? Is residual risk acceptable?",
      "evidence_ids": ["..."]
    }
  ],
  "unmitigated_risks": ["Risks where Blue Team had no effective response..."],
  "risk_matrix_summary": "Overall risk posture assessment...",
  "recommended_actions": ["Prioritized list of actions to reduce risk..."]
}
```

### Step 6: Generate Markdown Report / 生成 Markdown 报告

Generate a structured Markdown report for human consumption.

Output: `reports/debate_report.md` (inside workspace directory)

Structure:

```markdown
# Debate Report: <topic>
## Executive Summary
<executive_summary from Step 4.5>

## Decision Matrix
| Factor | Assessment | Confidence | Key Evidence |
|---|---|---|---|

## Verified Facts
| # | Claim | Status | Sources | Track |
|---|---|---|---|---|

## Contested Points
| # | Point | Pro Position | Con Position | Judge Assessment |
|---|---|---|---|---|

## Key Arguments by Round
### Round N
| Side | Core Argument | Strength | Key Evidence |
|---|---|---|---|

## Scenario Outlook
| Scenario | Probability | Trigger | Timeframe |
|---|---|---|---|

## Watchlist
| # | Item | Why It Matters | Monitor How |
|---|---|---|---|

## Evidence Inventory
| ID | Source | Type | Tier | Freshness | Track |
|---|---|---|---|---|---|

## Conclusion Profiles (if Red Team mode)
| Dimension | Assessment | Confidence |
|---|---|---|

## Methodology
- Rounds: N, Mode: balanced/red_team
- Evidence items: X, Sources verified: Y
- Generated: <timestamp>
```

## Output Principles / 输出原则

- **No total score / 不使用总分**: Use evidence states, not numerical ratings
- **Traceable / 可追溯**: Every conclusion links back to specific evidence and rounds
- **Balanced / 平衡**: Present contested points fairly with both sides represented
- **Actionable / 可行动**: Watchlist items should be specific enough to actually monitor
- **Honest about uncertainty / 诚实对待不确定性**: Clearly distinguish verified from probable from unverified
- **Bilingual / 双语**: User-facing summary includes both Chinese and English
