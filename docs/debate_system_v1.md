# Three-Agent Real-Time Debate System (Workflow-First) — v1

## 1. Project Positioning
This project builds **agent + skill workflows**, not traditional software-first architecture.

Decision order for all tasks:
1. Use LLM if the task is reading/judging/summarizing/classifying/extracting/decisioning content.
2. Reuse existing skills before writing code.
3. Write deterministic code only when LLM/skills cannot do it (I/O, scheduling, time-window math, API orchestration, hashing).

## 2. Goal and Success Criteria
### Goal
Run multi-round debates on a user topic with three isolated agents:
- Pro (strictly supports the motion)
- Con (strictly opposes the motion)
- Judge (neutral verifier)

### Success Criteria
- Conclusions are traceable to sources and timestamps.
- Real-time fact layer uses a strict 24-hour freshness window by default.
- Critical factual claims require cross-source confirmation.
- Judge performs independent second-pass verification.
- No user-facing total score; output uses evidence states.

## 3. Agent Roles
### Pro Agent
- Always supports the motion.
- Must rebut opponent points and add new arguments each round.
- Every factual claim must attach evidence references.

### Con Agent
- Always opposes the motion.
- Same structure and constraints as Pro.

### Judge Agent
- Never takes sides.
- Verifies citations, timeliness, and reasoning quality.
- Produces structured ruling and mandatory response points for the next round.

## 4. Source System: Truthfulness and Freshness
### Two Evidence Tracks
- **Fact Track (Real-time):** Used for current conclusions; 24h freshness hard gate.
- **Reasoning Track (Historical/Classical):** Used for mechanism explanation only, not as current factual proof.

### Twitter/X Policy
- Role: **signal layer only** (auxiliary evidence).
- A Twitter factual claim cannot be upgraded to verified fact without at least one independent non-social source.
- Persist fields: `tweet_id`, `author_id`, `created_at`, `captured_at`, `url`, `text_hash`.

### Core Verification Rules
- Critical claim => at least two independent sources.
- Out-of-window evidence => `stale`.
- Judge reruns verification independently (do not trust debaters’ single-pass citations).

## 5. Reasoning Model (Not “Collect + Argue” Only)
Every argument must follow a reasoning chain:

`Observed facts -> Mechanism -> Scenario implication -> Trigger conditions -> Falsification conditions`

Required behavior:
- Debaters attack each other’s causal chain, not only stance.
- Each round updates assumptions: upheld, weakened, invalidated.
- Judge audits causal validity (e.g., correlation != causation).

## 6. Historical / Classical Citations (Divergence with Control)
- Historical/classical references are explanation-layer only.
- Per-round share is capped (preferred <15% of content).
- Any analogy must include:
  - at least 2 similarities
  - at least 1 key structural difference
- Judge may mark analogy as “heuristic only” if invalid.

## 7. Round Workflow
1. Topic initialization (topic, rounds, horizon, freshness window).
2. Source ingestion and normalization.
3. Verification and claim ledger updates.
4. Debate round: Pro -> Con -> Judge.
5. Repeat rounds with mandatory response to Judge’s unresolved points.
6. Final report output.
7. Scheduled refresh (recommended every 6 hours); regenerate report on evidence-state change.

## 8. Core Skills (Recommended)
- `SourceIngest24h`
- `EvidenceVerify`
- `DebateTurn`
- `JudgeAudit`
- `FinalSynthesis`

## 9. Minimal Data Contracts
### EvidenceItem
- `evidence_id`
- `source_type`
- `url`
- `publisher`
- `published_at`
- `retrieved_at`
- `snippet`
- `hash`
- `credibility_tier`

### ClaimItem
- `claim_id`
- `speaker` (`pro`/`con`)
- `claim_type` (`fact`/`inference`/`analogy`)
- `claim_text`
- `evidence_ids[]`
- `status` (`verified`/`contested`/`unverified`/`stale`)
- `last_verified_at`
- `judge_note`

### FinalReport
- `verified_facts`
- `probable_conclusions`
- `contested_points`
- `to_verify`
- `scenario_outlook`
- `watchlist_24h`

## 10. Output Format (User-Facing)
No total score. Use:
- Verified Facts
- High-Probability Conclusions
- Contested Points
- Items Requiring Verification
- 24h Watchlist and reversal triggers

## 11. Acceptance Criteria (for Implementation Agent)
- At least 3 rounds run end-to-end.
- Stable structured outputs each round.
- No critical claim enters `verified` without cross-source validation.
- Evidence older than 24h is downgraded to `stale` for current fact conclusions.
- Twitter-only claims cannot directly become verified facts.
- Final report includes scenario triggers and falsification conditions.

## 12. Non-Goals (v1)
- No heavy frontend productization.
- No large multi-topic distributed orchestration.
- No auto-execution of financial or geopolitical actions.
- No user-facing scoreboards.
