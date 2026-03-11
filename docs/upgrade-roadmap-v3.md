# Critical Debater v3 — Upgrade Roadmap
# Critical Debater v3 — 升级路线图

## Changelog / 变更日志

| 时间 / Time | 作者 / Author | 变更 / Change |
|---|---|---|
| 2026-03-10 15:45 | Claude | Phase 4 增加 Conclusion Profile 多维结论画像 / Added Conclusion Profile system |
| 2026-03-10 15:15 | Claude | Phase 4 增加强制 PDF 输出（默认 executive summary PDF 5+页）/ Added mandatory PDF output |
| 2026-03-11 | Claude | v0.2.0 升级备注：Phase 4 PDF 输出改为 Markdown 报告 / v0.2.0 note: Phase 4 PDF output replaced with Markdown report |
| 2026-03-10 | Claude | 初始创建：4 Phase 升级路线图 / Initial creation: 4-phase upgrade roadmap |

---

## Overview / 概述

v2 → v3 升级目标：从"地缘政经专用辩论工具"变成"任意领域的深度分析引擎"。

Core upgrades across 4 phases:
1. **Parameterization + Domain Adaptation** — 参数化 + 领域适配
2. **Evidence Quality Enhancement** — 证据质量增强（Twitter 假新闻、冲突明细）
3. **Format Breakthrough** — 形式突破（历史智慧 + 想象力展开）
4. **Output Enhancement + Use Case Expansion** — 输出增强 + 场景扩展

---

## Phase 1: Parameterization + Domain Adaptation / 参数化 + 领域适配

> 所有后续 Phase 都依赖于此。这是地基。

### 1.1 Domain-Aware Config

`config.json` 新增字段：`domain`, `depth`, `evidence_scope`, `output_format`, `speculation_level`, `language`, `focus_areas`, `mode`

Credibility tier 按 domain 动态映射（LLM 语义判断，不硬编码 if-else）。

### 1.2 Debate Skill 参数化入口

支持 `--domain`, `--depth`, `--mode`, `--speculation` 等参数。未提供则 LLM 自动推断。

**改动 Skill 文件：** `debate/SKILL.md`, `source-ingest/SKILL.md`, data-contracts.md

---

## Phase 2: Evidence Quality Enhancement / 证据质量增强

### 2.1 Twitter/Social Media Enhanced Verification

三层过滤：LLM credibility pre-screen → verification urgency tagging → independent corroboration search

EvidenceItem 新增：`social_credibility_flag`, `verification_priority`, `corroboration_status`

### 2.2 Evidence Conflict Detail

ClaimItem 新增 `conflict_details[]`：记录具体来源分歧，不仅仅是一个 `contested` 标签。

### 2.3 Source Diversity Assessment

FinalReport 新增 `evidence_diversity_assessment`：地域、来源类型、立场分布。

**改动 Skill 文件：** `evidence-verify/SKILL.md`, `source-ingest/SKILL.md`, `claim-ledger-update/SKILL.md`, `final-synthesis/SKILL.md`, data-contracts.md

---

## Phase 3: Format Breakthrough / 形式突破

### 3.1 Historical Wisdom Section

DebateTurn 新增独立 `historical_wisdom` section（与 arguments[] 平级），标记 `weight: "advisory"`。

AnalogySafeguard 扩展双模式：严格论证模式 + 宽松历史引用模式。

### 3.2 Speculative Scenarios Section

DebateTurn 新增 `speculative_scenarios` section，受 `speculation_level` 参数控制。

FinalReport 新增 `speculative_frontier` section。

**改动 Skill 文件：** `debate-turn/SKILL.md`, `analogy-safeguard/SKILL.md`, `judge-audit/SKILL.md`, `final-synthesis/SKILL.md`, data-contracts.md

---

## Phase 4: Output Enhancement + Use Case Expansion / 输出增强 + 场景扩展

### 4.1 Tiered Report Output + Mandatory PDF + Conclusion Profile

`final-synthesis` 支持 `detail_level`：`one_liner`, `executive`, `full`

**报告输出：** ~~PDF 输出已在 v0.2.0 中移除~~。替代方案：每场辩论生成结构化 Markdown 报告 (`reports/debate_report.md`)，包含表格驱动的决策矩阵、已验证事实、争议点、场景展望和监控清单。
**Report output:** ~~PDF output was removed in v0.2.0~~. Replacement: each debate generates a structured Markdown report (`reports/debate_report.md`) with table-driven decision matrix, verified facts, contested points, scenario outlook, and watchlist.

**Conclusion Profile（结论画像）：** 每个主要结论提供 10 维度画像：概率、置信度、共识度、证据完整度、可逆性、时效窗口、影响幅度、因果清晰度、可操作性、可证伪性。远超单一概率判断。

### 4.2 Red Team Mode

Orchestrator `mode: "red_team"`：Con → Red Team, Pro → Blue Team

### 4.3 Debate Templates

`.claude/templates/` 预设配置：investment, risk-assessment, tech-decision, policy-analysis

**改动 Skill 文件：** `final-synthesis/SKILL.md`, `debate/SKILL.md`, orchestrator agent prompt

---

## Dependency Graph / 依赖关系

```
Phase 1 (参数化 + Domain)
  ↓
Phase 2 (证据质量) ←── 依赖 domain 信息
  ↓
Phase 3 (历史/想象力) ←── 依赖 speculation_level 参数
  ↓
Phase 4 (输出/场景) ←── 依赖前 3 个 Phase 的新字段
```

## Verification / 验证方式

- **Phase 1:** 用 tech 领域辩题验证 domain 适配
- **Phase 2:** 用含 Twitter 来源的辩题验证假新闻检测
- **Phase 3:** 用历史性辩题验证历史智慧和推演展开
- **Phase 4:** 验证 executive summary、red team 模式、模板加载
