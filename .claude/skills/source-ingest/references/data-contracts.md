# Data Contracts / 数据契约

All agents and skills reference these JSON schemas as the single source of truth.
所有 agent 和 skill 引用这些 JSON schema 作为唯一真相来源。

---

## EvidenceItem

An individual piece of evidence from a source.
来自来源的单条证据。

```json
{
  "evidence_id": "evi_<hash_first8>",
  "source_type": "web | twitter | academic | government | other",
  "url": "https://...",
  "publisher": "Publisher Name",
  "published_at": "2026-03-09T12:00:00Z",
  "retrieved_at": "2026-03-09T12:30:00Z",
  "snippet": "Relevant excerpt from source...",
  "hash": "<SHA-256 of snippet>",
  "credibility_tier": "tier1_authoritative | tier2_reputable | tier3_general | tier4_social",
  "freshness_status": "current | stale | timeless",
  "evidence_track": "fact | reasoning"
}
```

### Credibility Tiers / 可信度分级
- `tier1_authoritative`: Government agencies, central banks, major wire services (AP, Reuters) / 政府、央行、主要通讯社
- `tier2_reputable`: Major newspapers, established research institutions, peer-reviewed journals / 主要报纸、知名研究机构、同行评审期刊
- `tier3_general`: Blogs, smaller publications, industry reports, company press releases / 博客、小型出版物、行业报告、公司新闻稿
- `tier4_social`: Twitter/X, Reddit, forums, personal posts / Twitter、Reddit、论坛、个人帖子

### Freshness Status / 时效状态
- `current`: Source is recent enough to support current-state claims / 来源足够新，可支持当前状态声明
- `stale`: Source was used for a current-state claim but is now outdated / 来源用于当前状态声明但已过期
- `timeless`: Historical/mechanism/trend evidence; NEVER auto-downgraded / 历史/机制/趋势证据，永不自动降级

### Evidence Track / 证据轨道
- `fact`: Supports claims about the current state of the world / 支持关于当前世界状态的声明
- `reasoning`: Supports mechanism explanation, historical precedent, or trend analysis / 支持机制解释、历史先例或趋势分析

---

## ClaimItem

A factual or inferential claim made by a debater.
辩手提出的事实性或推理性声明。

```json
{
  "claim_id": "clm_<round>_<side>_<seq>",
  "round": 1,
  "speaker": "pro | con",
  "claim_type": "fact | inference | analogy",
  "claim_text": "The claim statement...",
  "evidence_ids": ["evi_abc12345", "evi_def67890"],
  "status": "verified | contested | unverified | stale",
  "last_verified_at": "2026-03-09T12:00:00Z",
  "judge_note": "Judge's assessment...",
  "mandatory_response": false
}
```

### Claim Status State Machine / 声明状态机

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
           ├───►contested◄───────┤
           │           │         │
           ├───►stale   │        │
           │           ├───►verified
           │           ├───►stale
           └───────────┘
```

Transitions / 转换:
- `unverified → verified`: Cross-source confirmed / 跨来源确认
- `unverified → contested`: Sources conflict / 来源冲突
- `unverified → stale`: Current-state source expired / 当前状态来源过期
- `verified → contested`: New contradicting evidence / 新的矛盾证据
- `verified → stale`: Fact-track source expired / 事实轨道来源过期
- `contested → verified`: Resolution with new evidence / 新证据解决争议
- `contested → stale`: All sources expired / 所有来源过期
- `stale → verified`: Fresh confirming source found / 找到新鲜确认来源

**Critical rule / 关键规则**: Reasoning-track claims (claim_type=analogy or evidence_track=reasoning) are NEVER auto-transitioned to `stale`.
推理轨道声明永不自动转换为 `stale`。

---

## DebateTurn (Pro/Con Turn Output)

Structured output from a single debate turn.
单次辩论回合的结构化输出。

```json
{
  "round": 1,
  "side": "pro | con",
  "arguments": [
    {
      "claim_text": "Main argument statement...",
      "claim_type": "fact | inference | analogy",
      "evidence_ids": ["evi_abc12345"],
      "reasoning_chain": {
        "observed_facts": "What data/events support this...",
        "mechanism": "Why does this cause that...",
        "scenario_implication": "What follows from this...",
        "trigger_conditions": "What would make this scenario happen...",
        "falsification_conditions": "What would prove this wrong..."
      }
    }
  ],
  "rebuttals": [
    {
      "target_claim_id": "clm_1_con_1",
      "rebuttal_text": "Counter-argument...",
      "evidence_ids": ["evi_def67890"]
    }
  ],
  "mandatory_responses": [
    {
      "point_id": "mrp_1_1",
      "response_text": "Addressing judge's point..."
    }
  ],
  "new_evidence": []
}
```

### Reasoning Chain (MANDATORY) / 推理链（必需）

Every argument MUST contain all 5 elements. Use semantic understanding, not mechanical templates.
每个论点必须包含全部 5 个要素。用语义理解构建，不要机械填模板。

1. **Observed facts / 观察到的事实**: Concrete data, events, or statistics
2. **Mechanism / 机制**: Causal explanation (why A leads to B)
3. **Scenario implication / 场景推演**: What follows if the mechanism holds
4. **Trigger conditions / 触发条件**: What would activate this scenario
5. **Falsification conditions / 证伪条件**: What would disprove this argument

---

## JudgeRuling

Judge's structured output after auditing a round.
裁判审计回合后的结构化输出。

```json
{
  "round": 1,
  "verification_results": [
    {
      "claim_id": "clm_1_pro_1",
      "original_status": "unverified",
      "new_status": "verified",
      "reasoning": "Cross-source confirmed by Reuters and Bloomberg..."
    }
  ],
  "causal_validity_flags": [
    {
      "claim_id": "clm_1_con_2",
      "issue": "correlation presented as causation",
      "severity": "critical | moderate | minor"
    }
  ],
  "mandatory_response_points": [
    {
      "point_id": "mrp_1_1",
      "target": "pro | con | both",
      "point": "What must be addressed...",
      "reason": "Why this needs response..."
    }
  ],
  "round_summary": "Neutral summary of key developments..."
}
```

---

## FinalReport

Final synthesis output after all debate rounds.
所有辩论回合后的最终综合输出。

```json
{
  "topic": "The debate topic",
  "total_rounds": 3,
  "generated_at": "2026-03-09T18:00:00Z",
  "verified_facts": [
    "Cross-source confirmed factual statements..."
  ],
  "probable_conclusions": [
    "High-confidence conclusions with qualifiers..."
  ],
  "contested_points": [
    "Points where both sides have strong arguments..."
  ],
  "to_verify": [
    "Claims needing further verification with suggested methods..."
  ],
  "scenario_outlook": {
    "base_case": "Most likely scenario based on verified facts...",
    "upside_triggers": ["Conditions that would improve outlook..."],
    "downside_triggers": ["Conditions that would worsen outlook..."],
    "falsification_conditions": ["What would invalidate base case..."]
  },
  "watchlist_24h": [
    {
      "item": "What to monitor...",
      "reversal_trigger": "What would change conclusions...",
      "monitoring_source": "Where to watch..."
    }
  ]
}
```

---

## Audit Trail Entry (JSONL) / 审计日志条目

Each line in `logs/audit_trail.jsonl` is an independent JSON object.
`logs/audit_trail.jsonl` 中每行是一个独立 JSON 对象。

```json
{"timestamp": "2026-03-09T12:00:00Z", "action": "workspace_initialized | round_started | pro_turn_complete | con_turn_complete | judge_ruling_complete | claim_status_changed | evidence_added | report_generated | refresh_triggered", "details": {}}
```
