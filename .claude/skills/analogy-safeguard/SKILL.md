---
name: analogy-safeguard
description: >
  This skill should be used when "validating historical analogies in a debate turn",
  "checking if an analogy meets structural requirements", "verifying analogy has enough
  similarities and differences", "assessing analogy content share percentage", or
  "auditing classical reference compliance". Validates historical analogy usage
  against structural and proportion rules.
  验证历史类比使用是否符合结构和比例规则。
version: 0.2.0
---

# AnalogySafeguard
# 历史类比安全检查

Validate that historical and classical analogies in debate turns comply with structural requirements and proportion limits.
验证辩论回合中的历史和经典类比是否符合结构要求和比例限制。

## When to Use / 何时使用

- During DebateTurn construction as self-check / DebateTurn 构建时作为自检
- During JudgeAudit to validate analogy usage / JudgeAudit 验证类比使用时
- When reviewing any argument that references historical precedent / 审查任何引用历史先例的论点时

## Input / 输入 (v3 update)

- `content`: The debate turn content to validate
- `mode`: "strict" | "advisory" (default: "strict")
  - `strict`: Used for analogies in `arguments[]` — full rules apply (≥2 similarities, ≥1 difference, <15% content share)
  - `advisory`: Used for `historical_wisdom` section — relaxed rules (requires `key_differences` and `applicability_caveat`, but no content share limit)

## Output / 输出

- Per analogy: `pass` | `fail` with reasons
- Overall content share assessment (strict mode only)
- Recommendations for failed analogies

## Validation Rules / 验证规则

### For `mode = "strict"` (arguments[]):

Current behavior unchanged:

#### Rule 1: Structural Requirements / 结构要求

Each historical or classical analogy MUST include:

**At least 2 similarities / 至少 2 个相似点**:
- Structural parallels between the historical case and current topic
- Not superficial similarities (e.g., "both involve money" is too vague)
- Must be causally relevant similarities

**At least 1 key structural difference / 至少 1 个关键结构差异**:
- An honest acknowledgment of where the analogy breaks down
- Must be substantive, not trivial
- This prevents over-reliance on historical parallels

If an analogy lacks either → **fail**, mark as "heuristic only"

#### Rule 2: Content Share / 内容占比

Total analogy and historical-reference content should be under ~15% of the debate turn's total content.

This is assessed by **LLM semantic judgment**, not mechanical word count:
- Estimate what proportion of the argument's substance relies on historical parallels
- A brief reference to a historical event is fine
- Building an entire argument primarily on historical analogy is too much

If content share exceeds ~15% → **flag** (not auto-fail; Judge decides)

#### Rule 3: Analogy Classification / 类比分类

Analogies that **pass** structural validation:
- Valid supporting evidence in the reasoning track
- Can be cited as part of the mechanism explanation

Analogies that **fail** structural validation:
- Marked as "heuristic only" by Judge
- Cannot serve as primary evidence for a claim
- The debater should be told to strengthen with non-analogy evidence

### For `mode = "advisory"` (historical_wisdom):

1. Verify `key_differences` field is substantive (not a token acknowledgment)
2. Verify `applicability_caveat` field is present and meaningful
3. NO content share limit — historical references can be explored in depth
4. Grade quality: "strong_parallel" | "moderate_parallel" | "weak_parallel"
5. If `weak_parallel`: suggest in output that the reference may not add value

## Workflow / 工作流

1. **Identify**: Use LLM to find all analogy sections in the debate turn
2. **Determine mode**: Check if the analogy is in `arguments[]` (strict) or `historical_wisdom` (advisory)
3. **Evaluate**: For each analogy, assess according to the appropriate mode
4. **Estimate**: Assess overall content share semantically (strict mode only)
5. **Report**: Return per-analogy pass/fail and overall assessment

## Examples of Good vs. Bad Analogies / 好坏类比示例

**Good / 好**: "The 2008 financial crisis (similarity 1: credit overextension, similarity 2: regulatory lag) suggests similar risks today, though the difference is that current regulatory frameworks are stronger post-Dodd-Frank."

**Bad / 坏**: "This is just like the 1929 crash" (no similarities articulated, no differences acknowledged)

**Bad / 坏**: "History always repeats itself" (not a structured analogy at all)
