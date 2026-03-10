---
name: judge-audit
description: >
  This skill should be used when the judge agent needs to "audit a debate round",
  "verify claims independently", "check causal validity of arguments", "produce a
  structured ruling", "identify mandatory response points for next round", "perform
  independent second-pass verification", or "evaluate reasoning quality from both sides".
  Independent verification, causal chain audit, and structured ruling generation.
  独立验证、因果链审计和结构化裁定生成。
version: 0.1.0
---

# JudgeAudit
# 裁判审计

Independent verification, causal chain audit, analogy validation, and structured ruling for a debate round.
独立验证、因果链审计、类比验证和辩论回合结构化裁定。

## When to Use / 何时使用

- After both Pro and Con have completed their turns in a round / 正反方均完成其回合后
- This is the Judge's primary workflow / 这是裁判的主要工作流
- See `references/data-contracts.md` for JudgeRuling output schema

## Input / 输入

- `pro_turn_path`: Path to rounds/round_N/pro_turn.json
- `con_turn_path`: Path to rounds/round_N/con_turn.json
- `evidence_store_path`: Path to evidence_store.json
- `claim_ledger_path`: Path to claim_ledger.json
- `round_number`: Current round

## Output / 输出

- `JudgeRuling` JSON written to rounds/round_N/judge_ruling.json
- Contains: verification_results, causal_validity_flags, mandatory_response_points, round_summary

## Core Workflow / 核心工作流

### Step 1: Independent Source Verification (CRITICAL) / 独立来源验证（关键）

**Do NOT trust debaters' citations at face value / 不要轻信辩手的引用**

For each factual claim from BOTH sides:

1. Read the claim and its referenced evidence_ids
2. Fetch the original evidence items from evidence_store
3. **Independently verify**: Use WebSearch and WebFetch to check:
   - Does the cited source actually support this claim? (not misquoted/out-of-context)
   - Is the source still accessible and current?
   - Are there counter-sources the debater didn't mention?
4. Use the EvidenceVerify skill with `independent_search = true`
5. Use FreshnessCheck to verify timeliness of fact-track claims
6. Produce a `verification_result` entry with recommended status transition

**Priority**: Focus verification effort on:
- Claims central to the argument (high impact)
- Claims with only one supporting source
- Claims using tier3/tier4 sources
- Claims where debater's reasoning seems to stretch the evidence

### Step 2: Causal Chain Audit / 因果链审计

For each argument's reasoning chain from both sides, evaluate:

1. **Observed facts**: Are they accurate? Are they cherry-picked?
2. **Mechanism**: Is the causal explanation logically sound?
   - Flag: correlation presented as causation
   - Flag: reverse causality
   - Flag: confounding variables ignored
   - Flag: mechanism relies on unstated assumptions
3. **Scenario implication**: Does it logically follow from the mechanism?
4. **Trigger conditions**: Are they specific and testable?
   - Flag: vague or unfalsifiable triggers
5. **Falsification conditions**: Are they genuinely falsifiable?
   - Flag: conditions that are impossible to test
   - Flag: conditions so broad they're meaningless

Produce `causal_validity_flags` for each issue found, with severity:
- `critical`: Fundamental logical flaw that invalidates the argument
- `moderate`: Weakness that significantly undermines the argument
- `minor`: Small issue that should be addressed but doesn't invalidate

### Step 3: Analogy Audit / 类比审计

Apply AnalogySafeguard rules to all historical/classical analogies:

1. Check structural requirements (≥2 similarities, ≥1 difference)
2. Assess content share proportion
3. Mark invalid analogies as "heuristic only" in the ruling

### Step 4: Mandatory Response Check / 必答点回应检查

If this is round 2+, verify that both sides addressed the previous round's mandatory response points:

1. Read previous round's judge_ruling mandatory_response_points
2. Check each debater's `mandatory_responses` array
3. Note any unaddressed points (the orchestrator should have caught this, but double-check)

### Step 5: Generate Mandatory Response Points / 生成必答点

Identify 2-5 points that MUST be addressed in the next round:

For each point:
- `point_id`: `mrp_<round>_<sequence>` (e.g., `mrp_1_1`)
- `target`: "pro" | "con" | "both"
- `point`: Clear statement of what must be addressed
- `reason`: Why this requires a response

**Types of mandatory response points / 必答点类型**:
- Unresolved factual contradictions between the sides
- Claims with critical causal validity issues
- New evidence that contradicts a key argument
- Weakly supported claims that need strengthening or withdrawal
- Questions raised by one side that the other didn't address

### Step 6: Round Summary / 回合总结

Write a neutral, balanced summary of the round:

- Key arguments from each side
- Which claims were verified, contested, or remain unverified
- The most important developments in this round
- No scoring, no preference — evaluate REASONING QUALITY, not which conclusion is "right"

### Step 7: Produce JudgeRuling JSON / 生成 JudgeRuling JSON

Assemble all outputs into the JudgeRuling schema and write to the designated path.
Validate with `scripts/validate-json.sh <file> judge_ruling`.

## Impartiality Rules (NON-NEGOTIABLE) / 公正规则（不可协商）

1. **NEVER** express preference for either side
2. Evaluate **reasoning quality**, not which conclusion you personally favor
3. Apply **identical standards** to both sides
4. If one side is clearly stronger this round, say so neutrally with evidence
5. **NEVER** use emotional language in the ruling
6. **NEVER** introduce your own arguments — only evaluate what was presented
7. Hold BOTH sides to the same evidence standards (tier requirements, cross-source, etc.)
