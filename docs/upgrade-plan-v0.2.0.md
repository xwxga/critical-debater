# Upgrade Plan: Skills v0.1.0 → v0.2.0
# 升级计划：Skills v0.1.0 → v0.2.0

## Changelog / 变更日志

| 时间 / Time | 作者 / Author | 变更 / Change |
|---|---|---|
| 2026-03-11 | Claude | 初始创建 / Initial creation |

---

## Context / 背景

当前 `.claude/skills/` 是 v0.1.0（v2 基线），`.agents/skills/` 是 v0.3.0（v3 升级后）。目标是将 `.claude/skills/` 升级到 **v0.2.0**，整合 v3 新功能，同时：
- 删除所有 PDF 功能，替换为结构化 Markdown 报告
- 删除 `pre_mortem` 幽灵模式
- 修复输出覆盖问题（workspace 路径动态化）
- 清理重复文件和过时内容

---

## Step 1: Upgrade 9 Skills to v0.2.0 / 升级 9 个 Skill 到 v0.2.0

Source: `.agents/skills/*/SKILL.md` (v0.3.0). Target: `.claude/skills/*/SKILL.md` (v0.2.0).

For each skill: copy v0.3.0 content, remove diff sections at top, set version to 0.2.0, apply per-skill modifications below.

| Skill | Source | Key Changes from v0.3.0 → v0.2.0 |
|---|---|---|
| **debate** | `.agents/skills/debate/SKILL.md` | Remove `--pdf` flag, remove `pre_mortem` from `--mode`, update paths `.agents/` → `.claude/`, remove template references (no templates exist) |
| **source-ingest** | `.agents/skills/source-ingest/SKILL.md` | Copy as-is (domain-aware + social pre-screen), version 0.2.0 |
| **freshness-check** | `.agents/skills/freshness-check/SKILL.md` | Copy as-is (no logic changes), version 0.2.0 |
| **evidence-verify** | `.agents/skills/evidence-verify/SKILL.md` | Copy as-is (Twitter corroboration), version 0.2.0 |
| **debate-turn** | `.agents/skills/debate-turn/SKILL.md` | Copy as-is (+Step 7 historical_wisdom, +Step 8 speculative_scenarios), version 0.2.0 |
| **judge-audit** | `.agents/skills/judge-audit/SKILL.md` | Copy as-is (+Step 1.6b, 3.5, 3.6), version 0.2.0 |
| **claim-ledger-update** | `.agents/skills/claim-ledger-update/SKILL.md` | Copy as-is (+conflict_details), version 0.2.0 |
| **analogy-safeguard** | `.agents/skills/analogy-safeguard/SKILL.md` | Copy as-is (+dual-mode), version 0.2.0 |
| **final-synthesis** | `.agents/skills/final-synthesis/SKILL.md` | Remove Step 5.5 (bilingual PDF data), Remove Step 6 (PDF generation), Remove PDF Content Principles, **Add new Step 6: Markdown Report Generation** (see below) |

### New Step 6 for final-synthesis: Markdown Report Generation

Output: `reports/debate_report.md` (inside workspace directory)

Structure (English only, table-driven):
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

## Step 2: Upgrade data-contracts.md / 升级数据契约

**File:** `.claude/skills/source-ingest/references/data-contracts.md`
**Source:** `.agents/skills/_shared/references/data-contracts.md` (v0.3.0)

Changes from v0.3.0:
- Version: 0.2.0
- **Remove**: `pdf_outputs`, `pdf_language` fields from DebateConfig
- **Remove**: `pre_mortem` from mode enum (keep only `balanced`, `red_team`)
- **Remove**: `RoundsBilingual` schema entirely
- **Add**: `report_path` field to FinalReport (path to generated markdown)
- **Keep all v3 fields**: social_credibility_flag, verification_priority, corroboration_status, conflict_details, historical_wisdom, speculative_scenarios, conclusion_profiles, etc.

## Step 3: Fix Output Overwrite / 修复输出覆盖问题

**File:** `.claude/agents/debate-orchestrator.md`

Replace all hardcoded `debate-workspace` references with dynamic path pattern:
- Format: `debates/<topic_slug>-<YYYYMMDD-HHMMSS>/`
- `topic_slug`: topic lowercased, spaces→hyphens, max 30 chars, alphanumeric+hyphens only
- Example: `debates/bitcoin-vs-gold-20260311-143022/`
- The orchestrator generates this path at debate start and passes it to `scripts/init-workspace.sh`
- `scripts/init-workspace.sh` already accepts dynamic `<dir>` as first arg — no changes needed there

## Step 4: Cleanup / 清理

1. **Delete** `.agents/skills/` directory (entire tree)
2. **Delete** `.agents/templates/` directory
3. **Delete** `scripts/generate_debate_pdf.py`
4. **Remove** `## v2 vs Current Diff` sections from all `.claude/skills/*/SKILL.md` (added previously, now obsolete after upgrade)

## Step 5: Update Documentation / 更新文档

1. **`docs/v2-vs-current-diff-report.md`**: Update to reflect post-upgrade state (single skill location, no PDF, dynamic workspace). Add changelog entry.
2. **`docs/upgrade-roadmap-v3.md`**: Note Phase 4 change: PDF → Markdown report.
3. **`.claude/CLAUDE.md`**: Update version references, note v0.2.0 upgrade. Add changelog entry.

## Step 6: Verification / 验证

- All `.claude/skills/*/SKILL.md` files have version 0.2.0
- No references to `.agents/skills/` remain in `.claude/` files
- No references to `pdf`, `PDF`, `generate_debate_pdf` remain in skills/agents
- No references to `pre_mortem` remain
- No hardcoded `debate-workspace` in orchestrator
- `data-contracts.md` has no `pdf_outputs`, `pdf_language`, `RoundsBilingual`, `pre_mortem`
- `.agents/skills/` and `.agents/templates/` deleted
- `scripts/generate_debate_pdf.py` deleted

---

## Execution Order / 执行顺序

1. Step 1 (skills) — can parallelize: 9 skills upgraded simultaneously
2. Step 2 (data-contracts) — after Step 1 (needs consistent references)
3. Step 3 (overwrite fix) — independent, can run with Step 2
4. Step 4 (cleanup/deletion) — after Steps 1-3 complete
5. Step 5 (docs) — after Step 4
6. Step 6 (verification) — last

---

## Critical Files / 关键文件

**Read (reference) / 读取（参考）:**
- `.agents/skills/*/SKILL.md` × 9 — v0.3.0 source for upgrade
- `.agents/skills/_shared/references/data-contracts.md` — v0.3.0 data contracts source
- `.claude/agents/debate-orchestrator.md` — for overwrite fix

**Modify / 修改:**
- `.claude/skills/*/SKILL.md` × 9 — upgrade to v0.2.0
- `.claude/skills/source-ingest/references/data-contracts.md` — upgrade to v0.2.0
- `.claude/agents/debate-orchestrator.md` — dynamic workspace path

**Delete / 删除:**
- `.agents/skills/` (entire directory)
- `.agents/templates/` (entire directory)
- `scripts/generate_debate_pdf.py`

**Update docs / 更新文档:**
- `docs/v2-vs-current-diff-report.md`
- `docs/upgrade-roadmap-v3.md`
- `.claude/CLAUDE.md`
