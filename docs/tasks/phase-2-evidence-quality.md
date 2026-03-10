# Phase 2: Evidence Quality Enhancement
# Phase 2: 证据质量增强

## Changelog / 变更日志

| 时间 / Time | 作者 / Author | 变更 / Change |
|---|---|---|
| 2026-03-10 | Claude | 初始创建 / Initial creation |

---

## Context / 背景

当前 Twitter 证据仅标记为"不能单独 verified"，没有主动的假新闻检测。
`contested` 状态只是一个标签，缺少具体冲突明细。
证据来源多样性无评估。

Depends on Phase 1 (domain field in config.json).

---

## Task 1: Extend EvidenceItem Schema for Social Media
## 任务 1：扩展 EvidenceItem Schema 支持社交媒体

**File:** `.claude/skills/source-ingest/references/data-contracts.md`

**Action:** Add 3 new optional fields to the EvidenceItem schema:

```json
{
  "evidence_id": "evi_<hash_first8>",
  "source_type": "web | twitter | academic | government | other",
  "url": "...",
  "publisher": "...",
  "published_at": "...",
  "retrieved_at": "...",
  "snippet": "...",
  "hash": "...",
  "credibility_tier": "...",
  "freshness_status": "...",
  "evidence_track": "...",
  "social_credibility_flag": "likely_reliable | needs_verification | likely_unreliable | null",
  "verification_priority": "high | medium | low",
  "corroboration_status": "corroborated | uncorroborated | contradicted | null"
}
```

Add documentation:
- `social_credibility_flag`: Only set for `source_type = "twitter"`. LLM pre-screens for fake news patterns. / 仅对 Twitter 来源设置。LLM 预筛假新闻特征。
- `verification_priority`: Derived from social_credibility_flag. `likely_unreliable` → `high`, `needs_verification` → `medium`, otherwise `low`. / 基于假新闻预筛结果推导。
- `corroboration_status`: Set during EvidenceVerify. Tracks whether independent non-social sources confirm this evidence. / 在 EvidenceVerify 中设置。追踪独立非社交来源是否确认。

---

## Task 2: Add Social Media Pre-Screen to SourceIngest
## 任务 2：在 SourceIngest 中添加社交媒体预筛

**File:** `.claude/skills/source-ingest/SKILL.md`

**Action:** Add a new step between Step 3 (Normalization) and Step 4 (Deduplication):

```markdown
### Step 3.5: Social Media Credibility Pre-Screen (v3) / 社交媒体可信度预筛

For each evidence item where `source_type = "twitter"`:

Use LLM to assess the tweet/post for fake news indicators:

**Check for these patterns / 检查以下特征:**
1. Extreme emotional language without factual basis / 无事实依据的极端情绪化语言
2. Claims without any cited sources or references / 没有引用任何来源的声明
3. Internal contradictions within the post / 帖子内部自相矛盾
4. Extraordinary claims without proportionate evidence / 非凡声明缺少相应的证据
5. Account context: is the publisher described as authoritative or unknown? / 发布者是否为已知权威来源

**Set `social_credibility_flag`:**
- `likely_reliable`: No fake news indicators, source appears authoritative
- `needs_verification`: Some indicators present, or source credibility unclear
- `likely_unreliable`: Multiple fake news indicators, high risk of misinformation

**Set `verification_priority`:**
- `likely_unreliable` → `high` (prioritize independent verification)
- `needs_verification` → `medium`
- `likely_reliable` → `low`

For non-Twitter sources, set these fields to `null`.
```

---

## Task 3: Enhance EvidenceVerify for Twitter Corroboration
## 任务 3：增强 EvidenceVerify 的 Twitter 关联验证

**File:** `.claude/skills/evidence-verify/SKILL.md`

**Action:** Enhance Step 3 (Twitter Signal Validation) with corroboration tracking:

Replace the current Step 3 with:

```markdown
### Step 3: Twitter Signal Validation + Corroboration (v3) / Twitter 信号验证 + 关联确认

If ANY evidence supporting a claim has `source_type = "twitter"`:

1. **Check social_credibility_flag** (set by SourceIngest):
   - If `likely_unreliable`: Flag claim as high verification priority. Auto-set status ceiling to `unverified` unless strong independent evidence exists.
   - If `needs_verification`: Standard verification process, but actively search for corroboration.

2. **Corroboration search** (enhanced from v2):
   - For `verification_priority = "high"` Twitter claims: ALWAYS run an independent WebSearch query derived from the claim text
   - Search specifically for non-social (tier1/tier2/tier3) sources that confirm or deny the claim
   - Update the Twitter EvidenceItem's `corroboration_status`:
     - `corroborated`: Found ≥1 independent non-social source confirming
     - `uncorroborated`: No independent confirmation found
     - `contradicted`: Found independent source(s) that directly contradict the claim

3. **Status determination** (unchanged logic, new data):
   - Twitter + corroborated → eligible for `verified` (if other conditions met)
   - Twitter + uncorroborated → maximum `unverified` with note "twitter-only, uncorroborated"
   - Twitter + contradicted → `contested` with note "twitter claim contradicted by [source]"
   - Twitter + `likely_unreliable` + uncorroborated → `unverified` with note "flagged (suspected misinformation)"
```

---

## Task 4: Add Conflict Details to ClaimItem Schema
## 任务 4：在 ClaimItem Schema 中添加冲突明细

**File:** `.claude/skills/source-ingest/references/data-contracts.md`

**Action:** Add `conflict_details` field to ClaimItem schema:

```json
{
  "claim_id": "clm_<round>_<side>_<seq>",
  "round": 1,
  "speaker": "pro | con",
  "claim_type": "fact | inference | analogy",
  "claim_text": "...",
  "evidence_ids": ["..."],
  "status": "verified | contested | unverified | stale",
  "last_verified_at": "...",
  "judge_note": "...",
  "mandatory_response": false,
  "conflict_details": [
    {
      "source_a": {"evidence_id": "evi_xxx", "position": "Source A claims..."},
      "source_b": {"evidence_id": "evi_yyy", "position": "Source B claims..."},
      "divergence_point": "The specific point of disagreement...",
      "judge_assessment": "Judge's evaluation of the conflict..."
    }
  ]
}
```

Add documentation: `conflict_details` is populated by Judge during verification when sources conflict. Allows FinalReport to explain WHY a claim is contested, not just THAT it is. / 当来源冲突时由 Judge 填充。让 FinalReport 能解释声明为何有争议，而不仅仅标记为有争议。

---

## Task 5: Update ClaimLedgerUpdate to Handle Conflict Details
## 任务 5：更新 ClaimLedgerUpdate 处理冲突明细

**File:** `.claude/skills/claim-ledger-update/SKILL.md`

**Action:** In the `batch_update` action workflow, add:

```markdown
3b. For each claim with `new_status = "contested"` in verification_results:
   - If the Judge's reasoning describes conflicting sources, extract and structure as `conflict_details`
   - Use LLM to identify: which evidence says what, and where exactly they diverge
   - Append to the claim's `conflict_details` array (don't overwrite existing conflicts)
```

---

## Task 6: Add Source Diversity Assessment to FinalSynthesis
## 任务 6：在 FinalSynthesis 中添加来源多样性评估

**File:** `.claude/skills/final-synthesis/SKILL.md`

**Action:** Add a new step between Step 4 (24h Watchlist) and Step 5 (Write Report):

```markdown
### Step 4.5: Source Diversity Assessment (v3) / 来源多样性评估

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

Also update the FinalReport schema in data-contracts.md to include `evidence_diversity_assessment`.

---

## Task 7: Update JudgeAudit to Populate Conflict Details
## 任务 7：更新 JudgeAudit 填充冲突明细

**File:** `.claude/skills/judge-audit/SKILL.md`

**Action:** In Step 1 (Independent Source Verification), add:

```markdown
6b. When independent verification reveals conflicting sources for a claim:
   - Document the conflict in the verification_result's `reasoning` field
   - Structure it as: "Source A (evi_xxx) states [position]. Source B (evi_yyy) states [position]. Divergence point: [specific disagreement]."
   - This structured reasoning will be extracted by ClaimLedgerUpdate into `conflict_details`
```

---

## Verification / 验证

After completing all tasks:

1. Read all modified files and verify schema consistency
2. Run a test debate on a topic with known Twitter controversy
   - Verify Twitter evidence gets `social_credibility_flag` assigned
   - Verify high-priority Twitter claims trigger independent corroboration search
   - Verify contested claims have `conflict_details` populated (not just a `contested` label)
   - Verify FinalReport includes `evidence_diversity_assessment`
3. Check that the `corroboration_status` field is properly set during EvidenceVerify
