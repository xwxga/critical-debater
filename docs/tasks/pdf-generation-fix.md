# PDF Generation Fix — Task Document
# PDF 生成修复 — 任务文档

## Changelog / 变更日志

| 时间 / Time | 作者 / Author | 变更 / Change |
|---|---|---|
| 2026-03-10 20:15 | Claude | 根据用户截图完全重写 PDF 布局设计：从冗长段落式改为信息密集表格驱动式 / Complete redesign based on user screenshots: from verbose paragraphs to dense table-driven layout |
| 2026-03-10 | Claude | 初始创建 / Initial creation |

---

## Background / 背景

Hormuz debate completed 3 rounds but no PDF was generated. Root causes:
Hormuz 辩论跑完 3 轮但没有生成 PDF。根本原因：

1. `scripts/generate_debate_pdf.py` — hardcoded paths + Iran-specific content + wrong layout style
   硬编码路径 + Iran 专用内容 + 错误的布局风格
2. DevContainer Dockerfile was missing `python3`, `pip`, `reportlab`, CJK fonts
   DevContainer 缺少 Python 运行时和字体
3. `generate-pdf.js` — another one-off script (midterms debate), should be deleted
   另一个一次性脚本，应删除

**Modify 1 (Dockerfile) already completed in main env.**
**修改 1（Dockerfile）已在主环境完成。**

---

## Target PDF Layout / 目标 PDF 布局

Based on the reference screenshots, the default PDF should be **information-dense, table-driven, Chinese-first**.
根据参考截图，默认 PDF 应该是**信息密集、表格驱动、中文优先**。

### Design Principles / 设计原则

1. **表格优先 / Tables first** — 几乎所有内容用表格呈现，不用段落文字
2. **信息压缩 / Compressed** — 每轮辩论压缩成表格中的一行，不展开每个论点的推理链
3. **攻防追踪 / Attack tracking** — 用颜色标记论点被攻击的状态
4. **中文优先 / Chinese-first** — 主体内容中文，关键术语附英文
5. **无花哨封面 / No ornate cover** — 直接从基本信息开始
6. **无目录 / No TOC** — 内容紧凑，不需要目录

### Page Layout / 页面布局

#### 第一部分：Executive Summary（1-2 页）

**Section 1: 基本信息 table**
```
┌──────────┬─────────────────────────────────────────────────┐
│ 项目     │ 内容                                             │
├──────────┼─────────────────────────────────────────────────┤
│ 辩题     │ <from config.topic>                              │
│ 轮次     │ <from config.round_count> 轮                     │
│ 正方模型  │ Claude Sonnet（立场：支持）                       │
│ 反方模型  │ Claude Sonnet（立场：反对）                       │
│ 裁判模型  │ Claude Opus（独立验证）                           │
│ 背景     │ <LLM summarizes from evidence_store context>     │
└──────────┴─────────────────────────────────────────────────┘
```

Data sources:
- 辩题: `config.json` → `topic`
- 轮次: `config.json` → `round_count`
- 背景: LLM generates from `evidence_store.json` context at report generation time. For the Python fallback script, read from `final_report.json` → look for a `background` or `context` field, or synthesize from `verified_facts[0..2]`.

**Section 2: 三轮辩论核心交锋 table**
```
┌──────┬──────────────────┬──────────────────┬──────────────────┐
│ 轮次 │ 正方核心论点       │ 反方核心论点       │ 裁判裁定          │
├──────┼──────────────────┼──────────────────┼──────────────────┤
│ 第一轮│ ① point1         │ ① point1         │ summary of       │
│      │ ② point2         │ ② point2         │ ruling           │
│      │ ③ point3         │ ③ point3         │                  │
├──────┼──────────────────┼──────────────────┼──────────────────┤
│ ...  │ ...              │ ...              │ ...              │
└──────┴──────────────────┴──────────────────┴──────────────────┘
```

Data sources per round:
- 正方核心论点: `rounds/round_N/pro_turn.json` → `arguments[].claim_text` (numbered ①②③)
- 反方核心论点: `rounds/round_N/con_turn.json` → `arguments[].claim_text`
- 裁判裁定: `rounds/round_N/judge_ruling.json` → `round_summary` (condensed)

**Section 3: 最终结论 table**
```
┌──────────┬──────┬──────────────────────────────────────────┐
│ 类别     │ 数量  │ 核心内容                                  │
├──────────┼──────┼──────────────────────────────────────────┤
│ 已验证事实│ N 条  │ comma-separated list of verified facts    │
│ 可能结论  │ N 条  │ comma-separated list of conclusions       │
│ 争议要点  │ N 条  │ comma-separated list of contested points  │
└──────────┴──────┴──────────────────────────────────────────┘
```

Data sources:
- `reports/final_report.json` → `verified_facts`, `probable_conclusions`, `contested_points`

**Section 4: 24小时监控清单 table**
```
┌──────────────────────┬───────────────────────────────┐
│ 监控项               │ 逆转触发条件                    │
├──────────────────────┼───────────────────────────────┤
│ item text            │ reversal trigger text          │
│ ...                  │ ...                           │
└──────────────────────┴───────────────────────────────┘
```

Data sources:
- `reports/final_report.json` → `watchlist_24h[]` → `.item` and `.reversal_trigger`

**Section 5: 总判断 (highlighted box)**

A single highlighted paragraph with the overall conclusion.
Data source: `reports/final_report.json` → `scenario_outlook.base_case`

---

#### 第二部分：轮次详情（每轮 1 页）

**Legend / 图例:**
```
🔴 被对方反驳 — 对手直接攻击的论点
🟠 被裁判质疑 — 裁判标记为"有争议"或因果链有漏洞
⚫ 被事实推翻 — 后续轮次中被新证据直接否定
```

Implementation note: use colored circles (reportlab drawing or Unicode ● with color) + text labels.

**Per-round exchange table / 每轮交锋表:**
```
┌────────────┬──────┬────────┬──────────────────┬──────────────────┐
│ 原始论点    │ 谁的 │ 被谁打  │ 怎么打的          │ 裁判怎么说        │
├────────────┼──────┼────────┼──────────────────┼──────────────────┤
│ claim_text │ 正方  │ 🔴反方  │ rebuttal summary │ judge reasoning  │
│            │      │ 🟠裁判  │                  │                  │
├────────────┼──────┼────────┼──────────────────┼──────────────────┤
│ ...        │      │        │                  │                  │
└────────────┴──────┴────────┴──────────────────┴──────────────────┘
```

Data sources per row:
- **原始论点**: `pro_turn.json` or `con_turn.json` → `arguments[].claim_text`
- **谁的**: "正方" or "反方"
- **被谁打**: Cross-reference:
  - 🔴反方反驳: Check if opponent's `rebuttals[].target_claim_id` matches this claim
  - 🟠裁判质疑: Check `judge_ruling.json` → `causal_validity_flags[]` or `verification_results[]` where `new_status = "contested"`
  - ⚫被事实推翻: Check later rounds' `verification_results[]` where status changed to something worse
- **怎么打的**: The rebuttal text or judge's issue description (condensed)
- **裁判怎么说**: `judge_ruling.json` → `verification_results[]` matching this claim → `.reasoning`

### How to Build the Attack Tracking / 攻防追踪构建方法

This is the most complex part. For each argument across all rounds:

```python
for each claim in pro_turn.arguments + con_turn.arguments:
    attacks = []

    # Check opponent rebuttals
    opponent_turn = con_turn if claim is from pro else pro_turn
    for reb in opponent_turn.rebuttals:
        if reb.target_claim_id == claim.claim_id:
            attacks.append(("反方反驳" or "正方反驳", reb.rebuttal_text))

    # Check judge flags
    for flag in judge_ruling.causal_validity_flags:
        if flag.claim_id == claim.claim_id:
            attacks.append(("裁判质疑", f"{flag.severity}: {flag.issue}"))

    # Check judge verification
    for vr in judge_ruling.verification_results:
        if vr.claim_id == claim.claim_id and vr.new_status in ("contested", "stale"):
            attacks.append(("裁判判定" + vr.new_status, vr.reasoning))

    # Check if overturned in later rounds
    # (compare claim status across rounds)
```

---

## Modify 2: Rewrite `scripts/generate_debate_pdf.py`
## 修改 2：重写 `scripts/generate_debate_pdf.py`

### Goal / 目标

Complete rewrite. Not a refactor of the old script — a new script with the table-driven layout described above.
完全重写。不是旧脚本的重构——是按照上述表格驱动布局的新脚本。

### Usage / 用法

```bash
python3 scripts/generate_debate_pdf.py <workspace_path> [output_filename]
```

- `workspace_path` (required): path to debate workspace
- `output_filename` (optional): defaults to `debate_report.pdf`

### Infrastructure Changes (keep from old plan) / 基础设施改动（保留旧 plan）

These apply regardless of layout changes:

#### 2a. CLI args instead of hardcoded paths

```python
import sys, glob
workspace = os.path.abspath(sys.argv[1])
output_name = sys.argv[2] if len(sys.argv) > 2 else "debate_report.pdf"
```

#### 2b. Cross-platform font detection

```python
def find_cjk_font():
    candidates = [
        # Linux (fonts-noto-cjk)
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJKsc-Regular.otf",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc",
        # macOS
        "/Library/Fonts/Arial Unicode.ttf",
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
    ]
    for path in candidates:
        if os.path.isfile(path):
            return path
    return None
```

Also try `fc-list :lang=zh file` as dynamic fallback on Linux.

#### 2c. translations.json optional

```python
tr_path = os.path.join(scripts_dir, "translations.json")
TR = load_json(tr_path) if os.path.isfile(tr_path) else {"claims":{}, ...}
```

All `TR[key].get(...)` → `TR.get(key, {}).get(...)`.

#### 2d. Read config from workspace

```python
config = load_json(os.path.join(workspace, "config.json"))
topic = config.get("topic", "Debate")
round_count = config.get("round_count", detect_round_count(workspace))
created_at = config.get("created_at", "")
```

### New Layout Implementation / 新布局实现

#### Structure overview / 结构概览

```python
def main():
    # 1. Parse args, load config, register font
    # 2. Load all round data + final report
    # 3. Build story:
    story = []
    build_basic_info_table(story, config)          # 基本信息
    build_round_overview_table(story, rounds_data)  # 三轮辩论核心交锋
    build_conclusions_table(story, final_report)    # 最终结论
    build_watchlist_table(story, final_report)      # 24小时监控清单
    build_overall_judgment(story, final_report)     # 总判断
    story.append(PageBreak())
    for r, (pro, con, judge) in enumerate(rounds_data, 1):
        build_round_detail(story, r, pro, con, judge, rounds_data)  # 每轮详情交锋表
    # 4. Build PDF
```

#### Key table: 三轮辩论核心交锋

This table condenses each round into one row. For claim_text that is too long, truncate or use LLM-style summarization in a pre-processing step.

Columns: `轮次 | 正方核心论点 | 反方核心论点 | 裁判裁定`

Each cell contains numbered points like `① claim1 ② claim2 ③ claim3`.

```python
def build_round_overview_table(story, rounds_data):
    header = ["轮次", "正方核心论点", "反方核心论点", "裁判裁定"]
    rows = [header]
    for r, (pro, con, judge) in enumerate(rounds_data, 1):
        cn = CN_NUMS.get(r, str(r))
        # Numbered claims, truncated
        pro_claims = "\n".join(
            f"① {a['claim_text'][:60]}" if i==0 else f"{CIRCLED_NUMS[i]} {a['claim_text'][:60]}"
            for i, a in enumerate(pro.get("arguments", []))
        )
        con_claims = "\n".join(...)
        judge_summary = judge.get("round_summary", "")[:200]
        rows.append([f"第{cn}轮", pro_claims, con_claims, judge_summary])
    # Build reportlab Table with word-wrap enabled
```

Use `Paragraph` objects inside table cells for word-wrap. Column widths: roughly `[12%, 30%, 30%, 28%]`.

#### Key table: 每轮交锋详情

This is the most complex table. For each round:

Columns: `原始论点 | 谁的 | 被谁打 | 怎么打的 | 裁判怎么说`

```python
def build_round_detail(story, round_num, pro, con, judge, all_rounds):
    # Title
    story.append(Paragraph(f"第{CN_NUMS[round_num]}轮交锋", title_style))

    # Build rows: one per argument from BOTH sides
    rows = [["原始论点", "谁的", "被谁打", "怎么打的", "裁判怎么说"]]

    all_args = []
    for arg in pro.get("arguments", []):
        all_args.append(("正方", arg, con, judge))
    for arg in con.get("arguments", []):
        all_args.append(("反方", arg, pro, judge))

    for side, arg, opponent, judge in all_args:
        claim_id = arg.get("claim_id", "")
        claim_text = arg.get("claim_text", "")[:80]

        # Find attacks
        attackers = []
        attack_details = []
        judge_says = []

        # Opponent rebuttals targeting this claim
        for reb in opponent.get("rebuttals", []):
            if reb.get("target_claim_id") == claim_id:
                opp_side = "反方" if side == "正方" else "正方"
                attackers.append(f"🔴 {opp_side}反驳")
                attack_details.append(reb.get("rebuttal_text", "")[:100])

        # Judge causal flags
        for flag in judge.get("causal_validity_flags", []):
            if flag.get("claim_id") == claim_id:
                attackers.append(f"🟠 裁判质疑")
                attack_details.append(f"{flag.get('severity','')}: {flag.get('issue','')}"[:100])

        # Judge verification
        for vr in judge.get("verification_results", []):
            if vr.get("claim_id") == claim_id:
                status = vr.get("new_status", "")
                if status in ("contested", "stale"):
                    attackers.append(f"🟠 裁判判定{status}")
                judge_says.append(vr.get("reasoning", "")[:150])

        rows.append([
            claim_text,
            side,
            "\n".join(attackers) or "—",
            "\n".join(attack_details) or "—",
            "\n".join(judge_says) or "—",
        ])
```

Column widths: `[20%, 8%, 12%, 30%, 30%]`

#### Color implementation / 颜色实现

For the attack markers in table cells:
- 🔴 use `<font color="#B71C1C">●</font>` + text in Paragraph
- 🟠 use `<font color="#E65100">●</font>` + text
- ⚫ use `<font color="#212121">●</font>` + text

#### reportlab table tips / reportlab 表格技巧

To enable word-wrap in table cells, use `Paragraph` objects instead of raw strings:

```python
# Each cell must be a Paragraph, not a string
cell = Paragraph(text, cell_style)

# Enable word wrap via Table style
t = Table(data, colWidths=[30*mm, 50*mm, 50*mm, 45*mm])
t.setStyle(TableStyle([
    ("VALIGN", (0,0), (-1,-1), "TOP"),
    ("FONTNAME", (0,0), (-1,-1), FONT_NAME),
    # header row
    ("BACKGROUND", (0,0), (-1,0), C_ACCENT),
    ("TEXTCOLOR", (0,0), (-1,0), white),
    # alternating rows
    ("ROWBACKGROUNDS", (0,1), (-1,-1), [white, HexColor("#F5F5F5")]),
    ("GRID", (0,0), (-1,-1), 0.5, C_DIVIDER),
]))
```

### What to Keep from Old Script / 从旧脚本保留的部分

- Color palette (C_PRO, C_CON, C_JUDGE, etc.) — good color choices
- `esc()` function — XML escaping for reportlab
- `make_colored_box()` — useful for 总判断 box
- `load_json()` — but add error handling (return {} on failure)
- `bilingual()` / `split_bilingual()` helpers

### What to Remove / 删除的部分

- Ornate cover page (`build_cover`) — replace with simple 基本信息 table
- TOC (`build_toc`) — remove entirely
- Verbose argument rendering (`build_argument`, `build_rebuttal`) — replace with condensed table rows
- Verbose judge rendering (per-verification, per-flag, per-MRP details) — condense into table cells
- Scenario outlook as separate section — condense into 总判断 box
- Closing page — remove or make minimal (1 line footer)

---

## Modify 3: Delete `generate-pdf.js`
## 修改 3：删除 `generate-pdf.js`

```bash
git rm generate-pdf.js
```

---

## Modify 4: Update `final-synthesis` SKILL.md
## 修改 4：更新 `final-synthesis` SKILL.md

**File:** `.claude/skills/final-synthesis/SKILL.md`

Two changes:

### 4a. Update PDF style description in Step 6

The current Step 6 describes a page-by-page layout (Title page, Key Findings pages, etc.). Replace with the new table-driven layout description.

Replace the content under "#### Default: Executive Summary PDF (ALWAYS generated)" with:

```markdown
Generate a table-driven, information-dense PDF with the following structure:

**Part 1: Executive Summary (1-2 pages)**
- 基本信息 table: 辩题, 轮次, 模型, 背景
- 三轮辩论核心交锋 table: one row per round with 正方/反方核心论点 + 裁判裁定
- 最终结论 table: 已验证事实/可能结论/争议要点 with counts and content
- 24小时监控清单 table: 监控项 + 逆转触发条件
- 总判断 highlighted box: base case assessment

**Part 2: Round Details (1 page per round)**
- Legend: 🔴被对方反驳 🟠被裁判质疑 ⚫被事实推翻
- Per-round exchange table: 原始论点 | 谁的 | 被谁打 | 怎么打的 | 裁判怎么说

**Style: 表格优先、信息压缩、中文优先、无花哨封面**
```

### 4b. Add Python fallback

After the `anthropic-skills:pdf` instruction, add:

```markdown
#### Fallback: Python PDF Script / 备用：Python PDF 脚本

If the `pdf` skill is not available or fails:
1. Run: `python3 scripts/generate_debate_pdf.py <workspace_path> executive_summary.pdf`
2. Verify output exists in `<workspace>/reports/executive_summary.pdf`
3. If Python script also fails, log error and continue — JSON reports are the primary output
```

---

## Verification Steps / 验证步骤

After all modifications, run in the dev container:

```bash
# 1. Confirm Python + reportlab
python3 -c "import reportlab; print('reportlab OK')"

# 2. Confirm CJK font available
fc-list | grep -i noto

# 3. Test with Hormuz workspace
python3 scripts/generate_debate_pdf.py debate-workspace-hormuz/

# 4. Check output
ls -la debate-workspace-hormuz/reports/debate_report.pdf

# 5. Open PDF and verify:
#    - 基本信息 table renders correctly
#    - 三轮核心交锋 table shows all 3 rounds
#    - 攻防标记 (🔴🟠⚫) renders with correct colors
#    - Chinese text renders correctly (CJK font working)
#    - No hardcoded Iran/Hormuz-specific content

# 6. Test with old workspace too
python3 scripts/generate_debate_pdf.py debate-workspace/

# 7. Confirm generate-pdf.js is gone
test -f generate-pdf.js && echo "STILL EXISTS" || echo "DELETED OK"
```

---

## Config.json Reference / config.json 参考

Two existing workspaces for testing:

**debate-workspace-hormuz/config.json:**
```json
{
  "topic": "3月底前,霍尔木兹海峡会重新的实质性开通 / The Strait of Hormuz will substantively reopen before end of March 2026",
  "round_count": 3,
  "created_at": "2026-03-10T03:15:35Z"
}
```

**debate-workspace/config.json:**
```json
{
  "topic": "Republican will sweep 2026 midterms",
  "round_count": 3,
  "domain": "geopolitics",
  "created_at": "2026-03-10T00:00:00Z"
}
```

---

## Reference Screenshots / 参考截图

The user provided screenshots showing the target PDF style. Key visual characteristics:
用户提供了目标 PDF 样式的截图。关键视觉特征：

1. **基本信息**: Simple 2-column key-value table, no borders just horizontal lines
2. **三轮核心交锋**: 4-column table, each round is one row, claims numbered with ①②③
3. **最终结论**: 3-column table (类别/数量/核心内容), dense text in 核心内容 column
4. **24h监控清单**: 2-column table (监控项/逆转触发条件)
5. **总判断**: Grey/beige highlighted box with bold conclusion text
6. **轮次详情**: 5-column table (原始论点/谁的/被谁打/怎么打的/裁判怎么说)
7. **攻防标记**: Colored circles (red/orange/black) inline with text
8. **Font style**: Clean, no-frills, similar to a professional consulting report
9. **Chinese-first**: All content primarily in Chinese
