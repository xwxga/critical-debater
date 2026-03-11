# v2 vs Current Implementation Diff Report
# v2 与当前实现差异报告

## Changelog / 变更日志

| 时间 / Time | 作者 / Author | 变更 / Change |
|---|---|---|
| 2026-03-11 | Claude | v0.2.0 升级后更新：单一 skill 位置、无 PDF、动态 workspace / Post v0.2.0 upgrade: single skill location, no PDF, dynamic workspace |
| 2026-03-11 | Claude | 初始创建：完整差异报告 / Initial creation: full diff report |

---

## 1. Overview / 概述

The Insight Debator system evolved from v2 design spec (`docs/debate_system_v2.md`) through a v3 upgrade roadmap (`docs/upgrade-roadmap-v3.md`). After the v0.2.0 upgrade, all skills reside in a single location:

Insight Debator 系统从 v2 设计文档经过 v3 升级路线图演进至当前状态。v0.2.0 升级后，所有 skill 统一存放在一个位置：

- **`.claude/skills/`** — v0.2.0 skills (consolidated from v3 features, PDF removed, pre_mortem removed)
- **`.claude/agents/`** — Agent definitions with dynamic workspace paths

### Evolution Path / 演进路径

```
v2 spec (docs/debate_system_v2.md)
  ↓ implemented as
v2 baseline (.claude/skills/ v0.1.0)
  ↓ v3 upgrade (temporary dual location)
v3 (.agents/skills/ v0.3.0 + .claude/skills/ v0.1.0)
  ↓ v0.2.0 consolidation
v0.2.0 current (.claude/skills/ only — single location, .agents/skills/ deleted)
```

### Key Changes in v0.2.0 / v0.2.0 关键变更

1. **Single skill location**: All skills consolidated into `.claude/skills/` (`.agents/skills/` deleted)
2. **No PDF generation**: PDF output replaced with structured Markdown report (`reports/debate_report.md`)
3. **No `pre_mortem` mode**: Mode options are `balanced` and `red_team` only
4. **Dynamic workspace paths**: Orchestrator generates unique paths (`debates/<topic_slug>-<YYYYMMDD-HHMMSS>/`) instead of hardcoded `debate-workspace/`
5. **No templates**: `.agents/templates/` directory removed (template system not yet implemented)
6. **All v3 features retained**: Domain-aware search, social media pre-screening, historical wisdom, speculative scenarios, conclusion profiles, evidence diversity assessment

---

## 2. Agent Layer Differences / Agent 层差异

### 2.1 Tool Set Changes / 工具集变化

| Agent | v2 Spec Tools | Current Implementation Tools | Delta |
|---|---|---|---|
| `pro-debater` | WebSearch, WebFetch, Read, Write | WebSearch, WebFetch, Read, Write, **Bash** | +Bash |
| `con-debater` | WebSearch, WebFetch, Read, Write | WebSearch, WebFetch, Read, Write, **Bash** | +Bash |
| `neutral-judge` | WebSearch, WebFetch, Read, Write, Grep | WebSearch, WebFetch, Read, Write, **Bash**, Grep | +Bash |
| `debate-orchestrator` | Read, Write, Glob, Grep, Agent, WebSearch | Read, Write, Glob, Grep, Agent, WebSearch, **WebFetch**, **Bash**, **TodoWrite** | +WebFetch, +Bash, +TodoWrite |

### 2.2 Dynamic Workspace (v0.2.0 new) / 动态工作区

The orchestrator now generates unique workspace paths at debate start:
- Format: `debates/<topic_slug>-<YYYYMMDD-HHMMSS>/`
- Prevents output overwrite between debate sessions
- `scripts/init-workspace.sh` already accepts dynamic `<dir>` as first arg

---

## 3. Skill Layer Differences / Skill 层差异

### 3.1 Summary Table / 总览表

| Skill | Version | Key v0.2.0 Features |
|---|---|---|
| debate | 0.2.0 | 8 CLI flags (no --pdf, no --template, no pre_mortem), Red Team mode |
| source-ingest | 0.2.0 | Domain-aware search, social media pre-screen |
| freshness-check | 0.2.0 | No logic changes from v3 |
| evidence-verify | 0.2.0 | Twitter corroboration, social_credibility_flag integration |
| debate-turn | 0.2.0 | Historical wisdom (Step 7), speculative scenarios (Step 8) |
| judge-audit | 0.2.0 | Conflict docs (Step 1.6b), historical wisdom assessment (Step 3.5), speculative review (Step 3.6) |
| claim-ledger-update | 0.2.0 | conflict_details field extraction |
| analogy-safeguard | 0.2.0 | Dual-mode (strict/advisory) |
| final-synthesis | 0.2.0 | Conclusion profiles, Markdown report (replaces PDF), no Step 5.5 bilingual round data |

---

## 4. Data Contract Differences / 数据契约差异

### v0.2.0 Changes from v0.3.0 / 与 v0.3.0 的差异

| Change | Detail |
|---|---|
| Removed `pdf_outputs` | No PDF generation |
| Removed `pdf_language` | No PDF generation |
| Removed `pre_mortem` from mode enum | Only `balanced` and `red_team` |
| Removed `RoundsBilingual` schema | No bilingual round data for PDF |
| Added `report_path` to FinalReport | Path to generated Markdown report |

### Retained v3 Fields / 保留的 v3 字段

All v3 data contract additions are retained: `social_credibility_flag`, `verification_priority`, `corroboration_status`, `conflict_details`, `historical_wisdom`, `speculative_scenarios`, `conclusion_profiles`, `evidence_diversity_assessment`, `speculative_frontier`, `historical_insights`, `verdict_summary`.

---

## 5. Infrastructure Differences / 基础设施差异

### 5.1 Report Output (v0.2.0) / 报告输出

| Aspect / 方面 | v0.1.0 | v0.2.0 Current / 当前 |
|---|---|---|
| Report output / 报告输出 | JSON only | JSON + structured Markdown report |
| Report file | `reports/final_report.json` | `reports/final_report.json` + `reports/debate_report.md` |
| PDF | Not present | Not present (removed from v0.3.0) |

### 5.2 Deleted Artifacts / 已删除的文件

- `.agents/skills/` — entire directory (consolidated into `.claude/skills/`)
- `.agents/templates/` — entire directory (template system not implemented)
- `scripts/generate_debate_pdf.py` — PDF generation script

---

## 6. Summary / 总结

v0.2.0 is a consolidation release that merges v3 capability additions into the canonical `.claude/skills/` location while removing PDF generation and the unimplemented `pre_mortem` mode. The system now uses structured Markdown reports and dynamic workspace paths.

v0.2.0 是一个整合版本，将 v3 的能力增强合并到规范的 `.claude/skills/` 位置，同时移除了 PDF 生成和未实现的 `pre_mortem` 模式。系统现在使用结构化 Markdown 报告和动态工作区路径。
