---
name: final-synthesis
description: >
  This skill should be used when the orchestrator needs to "generate the final debate report",
  "synthesize all rounds into a conclusion", "create the final output with watchlist and
  scenario outlook", "produce the debate summary", or "compile verified facts, contested
  points, and recommendations". Generates the final debate report from all rounds' data.
  从所有回合数据生成最终辩论报告。
version: 0.1.0
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
- Human-readable summary for the user (bilingual Chinese + English)

## Core Workflow / 核心工作流

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

### Step 5: Write Report / 写入报告

1. Assemble into FinalReport JSON schema
2. Write to `reports/final_report.json`
3. Validate with `scripts/validate-json.sh <file> final_report`
4. Log report generation via `scripts/append-audit.sh`

## Output Principles / 输出原则

- **No total score / 不使用总分**: Use evidence states, not numerical ratings
- **Traceable / 可追溯**: Every conclusion links back to specific evidence and rounds
- **Balanced / 平衡**: Present contested points fairly with both sides represented
- **Actionable / 可行动**: Watchlist items should be specific enough to actually monitor
- **Honest about uncertainty / 诚实对待不确定性**: Clearly distinguish verified from probable from unverified
- **Bilingual / 双语**: User-facing summary includes both Chinese and English
