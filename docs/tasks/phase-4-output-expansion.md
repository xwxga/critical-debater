# Phase 4: Output Enhancement + Use Case Expansion
# Phase 4: 输出增强 + 场景扩展

## Changelog / 变更日志

| 时间 / Time | 作者 / Author | 变更 / Change |
|---|---|---|
| 2026-03-10 15:45 | Claude | 添加 Conclusion Profile 多维结论画像体系 / Added multi-dimensional Conclusion Profile system |
| 2026-03-10 15:15 | Claude | 添加 PDF 输出要求：默认 executive summary PDF 5+页 / Added mandatory PDF output |
| 2026-03-10 | Claude | 初始创建 / Initial creation |

---

## Context / 背景

当前系统只有一种输出格式（full_report）和一种辩论模式（balanced）。
需要支持分层报告、红队模式、和辩论模板。

Depends on Phase 1 (`output_format`, `mode` config fields) and Phase 3 (`speculative_frontier`, `historical_insights` in FinalReport).

---

## Task 1: Tiered Report Output in FinalSynthesis
## 任务 1：FinalSynthesis 分层报告输出

**File:** `.claude/skills/final-synthesis/SKILL.md`

**Action:** Add output format handling based on `config.output_format`:

```markdown
### Step 0: Read Output Format (v3) / 读取输出格式

Read `config.json` for `output_format` field. This controls the report detail level.

### Output Format: `full_report` (default)
Current behavior — generate complete FinalReport with all sections.

### Output Format: `executive_summary`
Generate a condensed version:
1. One-paragraph summary of the debate conclusion (bilingual)
2. Top 3-5 verified facts (bullet points)
3. Top 2-3 contested points with one-sentence explanation each
4. Scenario outlook: base case + top 2 triggers only
5. Top 3 watchlist items

Write to `reports/executive_summary.json` AND `reports/final_report.json` (full version still generated for reference).

Present the executive summary to the user, with a note that the full report is available.

### Output Format: `decision_matrix`
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

```json
{
  "decision_matrix": {
    "dimensions": [
      {
        "factor": "Factor name",
        "pro_position": "Pro's strongest point on this factor",
        "con_position": "Con's strongest point on this factor",
        "evidence_strength": "strong | moderate | weak",
        "judge_note": "..."
      }
    ],
    "overall_lean": "Slightly favors pro/con because...",
    "key_uncertainty": "The factor most likely to change the conclusion...",
    "recommendation": "Based on current evidence..."
  }
}
```

Write to `reports/decision_matrix.json` AND `reports/final_report.json`.
```

Update the FinalReport schema in data-contracts.md to include optional `decision_matrix` and `executive_summary` fields.

---

## Task 1.2: Conclusion Profile System (Multi-Dimensional Conclusion Characterization)
## 任务 1.2：结论画像体系（多维结论刻画）

**Context:** 当前结论只有概率一个维度。需要为每个结论生成多维画像，让读者一眼理解"这个结论有多可靠、多稳定、多有用"。

**Files:**
- `.claude/skills/source-ingest/references/data-contracts.md` — FinalReport schema 增加 `conclusion_profiles[]`
- `.claude/skills/final-synthesis/SKILL.md` — 增加 Conclusion Profile 生成步骤
- `.claude/skills/judge-audit/SKILL.md` — Judge 为 claim 提供部分维度评估数据

### 1.2.1 Data Contract: ConclusionProfile Schema

在 data-contracts.md 的 FinalReport schema 中新增 `conclusion_profiles` 字段：

```json
{
  "conclusion_profiles": [
    {
      "conclusion_id": "concl_1",
      "conclusion_text": "结论描述（双语）",
      "source_claims": ["clm_1_pro_1", "clm_2_con_3"],
      "profile": {
        "probability": {
          "value": "high (>70%) | medium (30-70%) | low (<30%)",
          "rationale": "基于什么判断此概率"
        },
        "confidence": {
          "value": "high | medium | low",
          "rationale": "证据质量如何影响对概率判断的确定性"
        },
        "consensus": {
          "value": "high | partial | low",
          "rationale": "正反双方对此点的分歧程度"
        },
        "evidence_coverage": {
          "value": "complete | partial | sparse",
          "gaps": "证据链中缺失的关键环节"
        },
        "reversibility": {
          "value": "high | medium | low",
          "reversal_trigger": "什么新证据/事件能推翻此结论"
        },
        "validity_window": {
          "value": "hours | days | weeks | months | indefinite",
          "expiry_condition": "什么条件会让此结论失效"
        },
        "impact_magnitude": {
          "value": "extreme | high | medium | low",
          "scope": "影响的范围和深度"
        },
        "causal_clarity": {
          "value": "clear_chain | partial_chain | correlation_only",
          "weakest_link": "因果链中最薄弱的环节"
        },
        "actionability": {
          "value": "directly_actionable | informational | requires_more_data",
          "suggested_action": "如果可操作，建议的行动"
        },
        "falsifiability": {
          "value": "easily_testable | testable_with_effort | hard_to_test",
          "test_method": "如何验证此结论的对错"
        }
      }
    }
  ]
}
```

**Documentation / 文档：**

```markdown
### ConclusionProfile (v3) / 结论画像

Multi-dimensional characterization of each major conclusion. Goes far beyond probability alone.
每个主要结论的多维刻画。远超概率单一维度。

**10 dimensions / 10 个维度:**

| Dimension / 维度 | What it measures / 衡量什么 | Why it matters / 为什么重要 |
|---|---|---|
| Probability / 概率 | 事件发生可能性 | 最基本的判断 |
| Confidence / 置信度 | 对概率判断本身的确定性 | "70% 概率但低置信度" vs "70% 概率且高置信度" 含义完全不同 |
| Consensus / 共识度 | 正反双方分歧程度 | 高共识结论更稳固，低共识结论更有争议 |
| Evidence Coverage / 证据完整度 | 证据链完整性 | 发现盲区，知道哪些证据还缺 |
| Reversibility / 可逆性 | 新证据推翻结论的难易度 | 高可逆 = 结论不稳定，需持续关注 |
| Validity Window / 时效窗口 | 结论有效期 | 有些结论 48 小时后就可能过时 |
| Impact Magnitude / 影响幅度 | 如果发生的影响大小 | 低概率高影响 = 黑天鹅型，需要关注 |
| Causal Clarity / 因果清晰度 | 因果链完整性 | "相关性" vs "因果性" 的区分 |
| Actionability / 可操作性 | 能否指导行动 | 决策者需要的是可操作结论 |
| Falsifiability / 可证伪性 | 验证难易度 | 不可证伪的结论价值有限 |

**Key rule / 关键规则:** Each dimension uses LLM semantic judgment, NOT mechanical scoring.
每个维度用 LLM 语义判断，不要用机械评分。
```

### 1.2.2 FinalSynthesis: Generate Conclusion Profiles

在 `final-synthesis/SKILL.md` 中，在 Step 2 (Categorize Claims) 之后增加：

```markdown
### Step 2.5: Generate Conclusion Profiles (v3) / 生成结论画像

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
```

### 1.2.3 JudgeAudit: Provide Dimension Data

在 `judge-audit/SKILL.md` 的 Step 6 (Round Summary) 中增加：

```markdown
For each claim evaluated in this round, note in verification_results:
- Whether the causal chain is clear or has gaps (feeds into `causal_clarity`)
- Whether the claim has strong falsification conditions (feeds into `falsifiability`)
- How much new evidence would be needed to reverse the status (feeds into `reversibility`)

These notes will be consumed by FinalSynthesis when building Conclusion Profiles.
```

### 1.2.4 PDF Integration

Executive Summary PDF 中增加 Conclusion Profile 展示：

**在 Page 2-3 (Key Findings) 中：**
每个主要结论旁边展示其画像的核心维度（选最关键的 4-5 个维度），使用紧凑的表格或标签格式：

```
结论: "中东局势大概率升级 / Middle East escalation is highly probable"
┌─────────────────────────────────────────────────────┐
│ 概率 Probability: HIGH    置信度 Confidence: MEDIUM  │
│ 共识度 Consensus: LOW     可逆性 Reversibility: HIGH │
│ 时效窗口 Validity: 48h    影响 Impact: EXTREME       │
│ 证据完整度 Coverage: 75%  可操作性: INFORMATIONAL     │
└─────────────────────────────────────────────────────┘
```

---

## Task 1.5: Mandatory Executive Summary PDF Output (DEFAULT)
## 任务 1.5：强制 Executive Summary PDF 输出（默认行为）

**Context:** 每场辩论默认必须输出一个 5 页以上的 executive summary PDF。用户可通过 `--pdf full` 或 `--pdf decision_matrix` 选择额外生成其他格式的 PDF。

**Files:**
- `.claude/skills/final-synthesis/SKILL.md` — 增加 PDF 生成步骤
- `.claude/skills/source-ingest/references/data-contracts.md` — config schema 增加 `pdf_outputs` 字段
- `.claude/skills/debate/SKILL.md` — 增加 `--pdf` 参数

### 1.5.1 Config Schema Update

在 DebateConfig schema 中新增：
```json
{
  "pdf_outputs": ["executive_summary"],
  "pdf_language": "bilingual"
}
```
- `pdf_outputs` 默认值为 `["executive_summary"]`（始终包含）
- 用户可通过 `--pdf full,decision_matrix` 增加额外 PDF 输出
- `pdf_language` 默认 `"bilingual"`，可通过 `--language` 设置

### 1.5.2 Debate Skill Parameter Update

在 debate/SKILL.md 的参数解析中增加：
```markdown
- `--pdf <value>`: Comma-separated list of additional PDF outputs to generate.
  Default: executive_summary (ALWAYS generated, cannot be disabled)
  Additional options: full, decision_matrix, red_team
  Example: `--pdf full,decision_matrix` → generates executive_summary PDF + full report PDF + decision matrix PDF
```

### 1.5.3 FinalSynthesis PDF Generation Step

在 final-synthesis/SKILL.md 的 Step 5 (Write Report) 之后增加：

```markdown
### Step 6: Generate PDF Reports (v3 MANDATORY) / 生成 PDF 报告（v3 必需）

**This step is MANDATORY. Every debate MUST produce at least an executive summary PDF.**
**此步骤为必需。每场辩论必须至少产出一份 executive summary PDF。**

Use the `pdf` skill (anthropic-skills:pdf) to generate formatted PDF reports.

#### Default: Executive Summary PDF (ALWAYS generated)

Generate a professionally formatted PDF with the following structure (minimum 5 pages):

**Page 1: Title Page / 标题页**
- Debate topic (bilingual)
- Date and total rounds
- Domain and mode

**Page 2-3: Key Findings / 核心发现**
- Verified facts table (columns: Fact | Evidence Sources | Confidence)
- Probable conclusions with confidence qualifiers
- Top contested points with both sides' positions

**Page 4: Scenario Outlook / 情景展望**
- Base case description
- Upside/downside triggers table (columns: Trigger | Likelihood | Impact)
- Falsification conditions

**Page 5: Watchlist & Historical Insights / 监控清单与历史洞察**
- 24h watchlist table (columns: Item | Reversal Trigger | Monitoring Source)
- Key historical parallels (from historical_wisdom, if Phase 3 enabled)
- Speculative frontier highlights (if speculation_level != conservative)

**Page 6+ (if content warrants): Evidence Appendix / 证据附录**
- Evidence diversity assessment
- Source type distribution chart (text-based table)
- Conflict details for contested claims

**PDF formatting requirements / PDF 格式要求:**
- Use tables for structured data (NOT paragraph text for tabular information)
- Bilingual headers: Chinese first, English second
- Professional font, clean layout
- Page numbers in footer
- Include debate metadata in header (topic, date, domain)

Write to: `reports/executive_summary.pdf`

#### Optional: Additional PDF Outputs

If `config.pdf_outputs` includes additional formats:

- `full`: Generate complete report as PDF (all sections, 10+ pages)
  → Write to: `reports/full_report.pdf`
- `decision_matrix`: Generate decision matrix as PDF (table-heavy format)
  → Write to: `reports/decision_matrix.pdf`
- `red_team`: Generate risk assessment as PDF (when mode=red_team)
  → Write to: `reports/risk_assessment.pdf`
```

### 1.5.4 PDF Quality Guidelines

```markdown
**PDF Content Principles / PDF 内容原则:**
- 表格优先：所有结构化数据用表格呈现，不要用段落文字描述表格式内容
  Tables first: Present all structured data as tables, not paragraph text
- 信息密度：PDF 不是 JSON 的美化版，而是为人类阅读优化的报告
  Information density: PDF is a human-optimized report, not a prettified JSON
- 可追溯：关键结论标注来源 evidence_id，让读者可以回溯到原始证据
  Traceable: Key conclusions reference evidence_ids for source tracing
- 双语：所有标题和关键术语双语呈现（中文优先）
  Bilingual: All headers and key terms in both languages (Chinese first)
```

---

## Task 2: Red Team Mode
## 任务 2：红队模式

**File:** `.claude/skills/debate/SKILL.md`

**Action:** Add Red Team mode handling in the orchestrator launch prompt:

```markdown
### Mode: `red_team`

When `config.mode = "red_team"`, the debate structure changes:

- **Con agent becomes Red Team**: Instead of opposing a motion, it actively searches for risks, vulnerabilities, failure modes, and blind spots in the topic/plan.
- **Pro agent becomes Blue Team**: Instead of supporting a motion, it defends against Red Team attacks with mitigations, contingency plans, and risk acceptance rationale.
- **Judge agent**: Evaluates the SEVERITY and LIKELIHOOD of each identified risk, and the FEASIBILITY of proposed mitigations.

**Orchestrator prompt adjustment:**
```
Run a Red Team analysis.

Topic: <parsed topic>
Mode: red_team
...

IMPORTANT MODE CHANGE:
- Con agent's role: RED TEAM — find every possible risk, failure mode, vulnerability, and blind spot. Be creative and thorough. Think about edge cases, cascading failures, adversarial scenarios, and black swan events.
- Pro agent's role: BLUE TEAM — for each risk identified by Red Team, propose mitigations, assess residual risk, and provide risk acceptance rationale where mitigation is impractical.
- Judge's role: Assess each risk's severity (critical/high/medium/low) and likelihood (high/medium/low). Evaluate whether Blue Team's mitigations are feasible and sufficient.
```
```

**File:** `.claude/skills/final-synthesis/SKILL.md`

**Action:** Add Red Team output format:

```markdown
### Red Team Report Format (v3) / 红队报告格式

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
```

---

## Task 3: Debate Templates
## 任务 3：辩论模板

**Action:** Create template files in `.claude/templates/`:

**File:** `.claude/templates/investment.json`
```json
{
  "template_name": "Investment Decision / 投资决策",
  "description": "Structured analysis for investment decisions with financial data focus",
  "config_overrides": {
    "domain": "finance",
    "depth": "deep",
    "mode": "balanced",
    "speculation_level": "moderate",
    "output_format": "decision_matrix",
    "focus_areas": ["valuation", "risk factors", "market conditions", "competitive landscape"]
  }
}
```

**File:** `.claude/templates/risk-assessment.json`
```json
{
  "template_name": "Risk Assessment / 风险评估",
  "description": "Red team analysis to identify and evaluate risks",
  "config_overrides": {
    "domain": "general",
    "depth": "deep",
    "mode": "red_team",
    "speculation_level": "exploratory",
    "output_format": "full_report",
    "focus_areas": ["failure modes", "cascading risks", "black swans"]
  }
}
```

**File:** `.claude/templates/tech-decision.json`
```json
{
  "template_name": "Tech Decision / 技术选型",
  "description": "Technology comparison and selection analysis",
  "config_overrides": {
    "domain": "tech",
    "depth": "standard",
    "mode": "balanced",
    "speculation_level": "moderate",
    "output_format": "decision_matrix",
    "focus_areas": ["performance", "ecosystem", "learning curve", "long-term viability"]
  }
}
```

**File:** `.claude/templates/policy-analysis.json`
```json
{
  "template_name": "Policy Analysis / 政策分析",
  "description": "Geopolitical or policy analysis with deep evidence verification",
  "config_overrides": {
    "domain": "geopolitics",
    "depth": "deep",
    "mode": "balanced",
    "speculation_level": "moderate",
    "output_format": "full_report",
    "focus_areas": ["stakeholder interests", "historical precedent", "implementation feasibility"]
  }
}
```

**File:** `.claude/skills/debate/SKILL.md`

**Action:** Add template support to argument parsing:

```markdown
### Template Support (v3) / 模板支持

If the user provides `--template <name>`:
1. Read `.claude/templates/<name>.json`
2. Apply `config_overrides` as default values
3. User-provided flags override template defaults
4. If template file not found, warn user and proceed with standard defaults

Examples:
- `/debate "Should we invest in NVIDIA?" --template investment`
  → Applies investment template: domain=finance, depth=deep, output=decision_matrix
- `/debate "Should we invest in NVIDIA?" --template investment --depth quick`
  → Same as above but overrides depth to quick
```

---

## Verification / 验证

After completing all tasks:

1. Verify template files exist and have valid JSON
2. Test tiered output:
   - `/debate "test topic" --output executive_summary` → verify condensed output
   - `/debate "test topic" --output decision_matrix` → verify matrix format
3. Test red team mode:
   - `/debate "Our plan to launch product X" --mode red_team` → verify Con acts as Red Team, output is risk assessment format
4. Test template loading:
   - `/debate "NVIDIA stock" --template investment` → verify config inherits template values
   - `/debate "NVIDIA stock" --template investment --depth quick` → verify user override works
5. Verify full_report still works as default (no regression)
6. **PDF output verification (CRITICAL):**
   - Run ANY debate → verify `reports/executive_summary.pdf` is generated (mandatory)
   - Verify PDF has ≥5 pages
   - Verify PDF uses tables for structured data (not paragraph text)
   - Verify PDF is bilingual (Chinese headers + English)
   - Test `--pdf full` → verify additional `reports/full_report.pdf` is generated
   - Test `--pdf decision_matrix` → verify `reports/decision_matrix.pdf` is generated
