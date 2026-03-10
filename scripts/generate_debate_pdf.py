#!/usr/bin/env python3
"""
Generate a table-driven, information-dense debate PDF report.
生成表格驱动、信息密集的辩论 PDF 报告。

Usage: python3 scripts/generate_debate_pdf.py <workspace_path> [output_filename]
"""

import json
import glob
import os
import subprocess
import sys
import urllib.request

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, white, black
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak,
    Table, TableStyle, HRFlowable,
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# ── Colors ──
C_PRO = HexColor("#1B5E20")
C_PRO_BG = HexColor("#E8F5E9")
C_CON = HexColor("#B71C1C")
C_CON_BG = HexColor("#FFEBEE")
C_JUDGE = HexColor("#E65100")
C_JUDGE_BG = HexColor("#FFF3E0")
C_TITLE = HexColor("#1A237E")
C_BODY = HexColor("#212121")
C_MUTED = HexColor("#616161")
C_ACCENT = HexColor("#0D47A1")
C_DIVIDER = HexColor("#BDBDBD")
C_HIGHLIGHT_BG = HexColor("#F5F5F5")

# ── Constants ──
CIRCLED_NUMS = ["①", "②", "③", "④", "⑤", "⑥", "⑦", "⑧", "⑨", "⑩"]
CN_NUMS = {1: "一", 2: "二", 3: "三", 4: "四", 5: "五", 6: "六"}

FONT_NAME = "CJKFont"
FONT_NAME_BOLD = "CJKFontBold"
PAGE_W, PAGE_H = A4
CONTENT_W = PAGE_W - 40 * mm  # 20mm margins each side

# Google Fonts TTF download URL for NotoSansSC variable weight
NOTO_SANS_SC_URL = "https://github.com/google/fonts/raw/main/ofl/notosanssc/NotoSansSC%5Bwght%5D.ttf"
FONT_CACHE_DIR = os.path.join(os.path.expanduser("~"), ".cache", "debate-fonts")


def esc(text):
    """XML-escape text for reportlab Paragraph."""
    if not text:
        return ""
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )


def load_json(path):
    """Load JSON file, return empty dict on failure."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Warning: failed to load {path}: {e}")
        return {}


# ═════════════════════════════════════════════════════════════
# Font detection and registration
# ═════════════════════════════════════════════════════════════

def find_cjk_font():
    """Cross-platform CJK TTF font detection."""
    candidates = [
        # Cached download
        os.path.join(FONT_CACHE_DIR, "NotoSansSC.ttf"),
        # Linux system fonts (TTF/TTC only — OTF with CFF outlines not supported by reportlab)
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansSC-Regular.ttf",
        # macOS
        "/Library/Fonts/Arial Unicode.ttf",
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
    ]
    for path in candidates:
        if os.path.isfile(path):
            return path

    # Dynamic fallback: fc-list for TTF/TTC only
    try:
        result = subprocess.run(
            ["fc-list", ":lang=zh", "file"],
            capture_output=True, text=True, timeout=5
        )
        for line in result.stdout.strip().split("\n"):
            path = line.strip().rstrip(":")
            if os.path.isfile(path) and (path.endswith(".ttf") or path.endswith(".ttc")):
                return path
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return None


def download_noto_font():
    """Download NotoSansSC TTF from Google Fonts as last resort."""
    cache_path = os.path.join(FONT_CACHE_DIR, "NotoSansSC.ttf")
    if os.path.isfile(cache_path):
        return cache_path
    print(f"Downloading NotoSansSC TTF font...")
    try:
        os.makedirs(FONT_CACHE_DIR, exist_ok=True)
        urllib.request.urlretrieve(NOTO_SANS_SC_URL, cache_path)
        if os.path.isfile(cache_path) and os.path.getsize(cache_path) > 1_000_000:
            print(f"Font downloaded to {cache_path}")
            return cache_path
        else:
            os.remove(cache_path)
    except Exception as e:
        print(f"Font download failed: {e}")
    return None


def register_fonts():
    """Register CJK fonts. Returns True on success."""
    global FONT_NAME, FONT_NAME_BOLD

    font_path = find_cjk_font()
    if not font_path:
        font_path = download_noto_font()
    if not font_path:
        return False

    print(f"Using font: {font_path}")
    pdfmetrics.registerFont(TTFont(FONT_NAME, font_path))
    # Note: Same font for bold — most CJK TTF fonts don't ship a separate bold weight.
    # reportlab uses synthetic bold via <b> tag, which is acceptable for table headers.
    pdfmetrics.registerFont(TTFont(FONT_NAME_BOLD, font_path))
    return True


# ═════════════════════════════════════════════════════════════
# Styles
# ═════════════════════════════════════════════════════════════

def detect_round_count(workspace):
    """Auto-detect number of rounds from directory structure."""
    rounds_dir = os.path.join(workspace, "rounds")
    if not os.path.isdir(rounds_dir):
        return 0
    return len(glob.glob(os.path.join(rounds_dir, "round_*")))


def S(name, **overrides):
    """Create a ParagraphStyle with CJK font."""
    defaults = {
        "fontName": FONT_NAME,
        "fontSize": 9,
        "leading": 14,
        "textColor": C_BODY,
        "alignment": TA_LEFT,
        "spaceAfter": 2 * mm,
        "wordWrap": "CJK",
    }
    defaults.update(overrides)
    return ParagraphStyle(name, **defaults)


ST = {}


def init_styles():
    global ST
    ST = {
        "title": S("title", fontSize=16, leading=22, textColor=C_TITLE,
                    spaceAfter=4 * mm, fontName=FONT_NAME_BOLD),
        "h2": S("h2", fontSize=12, leading=18, textColor=C_ACCENT,
                 spaceAfter=3 * mm, spaceBefore=4 * mm, fontName=FONT_NAME_BOLD),
        "cell": S("cell", fontSize=8, leading=12, spaceAfter=0),
        "cell_header": S("cell_header", fontSize=8, leading=12, textColor=white,
                          spaceAfter=0, fontName=FONT_NAME_BOLD),
        "cell_pro": S("cell_pro", fontSize=8, leading=12, textColor=C_PRO, spaceAfter=0),
        "cell_con": S("cell_con", fontSize=8, leading=12, textColor=C_CON, spaceAfter=0),
        "cell_sm": S("cell_sm", fontSize=7, leading=10, spaceAfter=0),
        "body": S("body", fontSize=9, leading=14),
        "highlight": S("highlight", fontSize=10, leading=16, fontName=FONT_NAME_BOLD),
        "legend": S("legend", fontSize=8, leading=12, textColor=C_MUTED),
    }


# ═════════════════════════════════════════════════════════════
# Helpers
# ═════════════════════════════════════════════════════════════

def safe_str(text):
    """Convert to string safely. No truncation — let reportlab Paragraph handle wrapping."""
    if not text:
        return ""
    return str(text)


def make_table(data, col_widths, extra_styles=None):
    """Build a styled Table with standard formatting."""
    t = Table(data, colWidths=col_widths, repeatRows=1)
    style_cmds = [
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("FONTNAME", (0, 0), (-1, -1), FONT_NAME),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("LEADING", (0, 0), (-1, -1), 12),
        # Header
        ("BACKGROUND", (0, 0), (-1, 0), C_ACCENT),
        ("TEXTCOLOR", (0, 0), (-1, 0), white),
        # Alternating rows
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [white, C_HIGHLIGHT_BG]),
        # Grid
        ("GRID", (0, 0), (-1, -1), 0.5, C_DIVIDER),
        # Padding
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]
    if extra_styles:
        style_cmds.extend(extra_styles)
    t.setStyle(TableStyle(style_cmds))
    return t


# Attack marker helpers — use <font color> inline HTML for colored markers
def red_marker(text):
    return f'<font color="#B71C1C">[R]</font> {esc(text)}'


def orange_marker(text):
    return f'<font color="#E65100">[J]</font> {esc(text)}'


def black_marker(text):
    return f'<font color="#212121">[X]</font> {esc(text)}'


# ═════════════════════════════════════════════════════════════
# Section builders
# ═════════════════════════════════════════════════════════════

def build_basic_info_table(story, config, final_report):
    """Section 1: 基本信息 table."""
    story.append(Paragraph("辩论报告 Debate Report", ST["title"]))
    story.append(Spacer(1, 2 * mm))

    topic = config.get("topic", "Debate")
    round_count = config.get("round_count", 0)
    created_at = config.get("created_at", "")[:10]

    # Background from first verified fact (may be string or dict)
    vf = final_report.get("verified_facts", [])
    if vf:
        first = vf[0]
        background = safe_str(first if isinstance(first, str) else first.get("fact", str(first)))
    else:
        background = ""

    info_rows = [
        ("辩题 Topic", topic),
        ("轮次 Rounds", f"{round_count} 轮"),
        ("日期 Date", created_at),
        ("正方 Pro", config.get("pro_model", "辩论正方 Pro Side")),
        ("反方 Con", config.get("con_model", "辩论反方 Con Side")),
        ("裁判 Judge", config.get("judge_model", "独立裁判 Independent Judge")),
        ("背景 Context", background),
    ]

    rows = [
        [Paragraph("<b>项目 Item</b>", ST["cell_header"]),
         Paragraph("<b>内容 Content</b>", ST["cell_header"])],
    ]
    for label, value in info_rows:
        rows.append([
            Paragraph(esc(label), ST["cell"]),
            Paragraph(esc(value), ST["cell"]),
        ])

    col_widths = [30 * mm, CONTENT_W - 30 * mm]
    story.append(make_table(rows, col_widths))
    story.append(Spacer(1, 4 * mm))


def build_round_overview_table(story, rounds_data):
    """Section 2: 三轮辩论核心交锋 table."""
    story.append(Paragraph("核心交锋 Core Clashes", ST["h2"]))

    header = [
        Paragraph("<b>轮次</b>", ST["cell_header"]),
        Paragraph("<b>正方核心论点 Pro Claims</b>", ST["cell_header"]),
        Paragraph("<b>反方核心论点 Con Claims</b>", ST["cell_header"]),
        Paragraph("<b>裁判裁定 Ruling</b>", ST["cell_header"]),
    ]
    rows = [header]

    for r, (pro, con, judge) in enumerate(rounds_data, 1):
        cn = CN_NUMS.get(r, str(r))

        pro_claims = "<br/>".join(
            f"{CIRCLED_NUMS[i]} {esc(safe_str(a.get('claim_text', '')))}"
            for i, a in enumerate(pro.get("arguments", []))
            if i < len(CIRCLED_NUMS)
        )
        con_claims = "<br/>".join(
            f"{CIRCLED_NUMS[i]} {esc(safe_str(a.get('claim_text', '')))}"
            for i, a in enumerate(con.get("arguments", []))
            if i < len(CIRCLED_NUMS)
        )
        judge_summary = esc(safe_str(judge.get("round_summary", "")))

        rows.append([
            Paragraph(f"R{r}", ST["cell"]),
            Paragraph(pro_claims, ST["cell_pro"]),
            Paragraph(con_claims, ST["cell_con"]),
            Paragraph(judge_summary, ST["cell_sm"]),
        ])

    col_widths = [12 * mm, 0.30 * CONTENT_W, 0.30 * CONTENT_W, CONTENT_W - 12 * mm - 0.60 * CONTENT_W]
    story.append(make_table(rows, col_widths))
    story.append(Spacer(1, 4 * mm))


def build_conclusions_table(story, final_report):
    """Section 3: 最终结论 table."""
    story.append(Paragraph("最终结论 Conclusions", ST["h2"]))

    header = [
        Paragraph("<b>类别 Category</b>", ST["cell_header"]),
        Paragraph("<b>数量 Count</b>", ST["cell_header"]),
        Paragraph("<b>核心内容 Key Content</b>", ST["cell_header"]),
    ]

    vf = final_report.get("verified_facts", [])
    pc = final_report.get("probable_conclusions", [])
    cp = final_report.get("contested_points", [])

    def summarize_list(items, max_items=3):
        parts = [esc(safe_str(item)) for item in items[:max_items]]
        if len(items) > max_items:
            parts.append(f"... ({len(items)} total)")
        return "<br/>".join(parts)

    rows = [
        header,
        [Paragraph("已验证事实 Verified", ST["cell"]),
         Paragraph(str(len(vf)), ST["cell"]),
         Paragraph(summarize_list(vf), ST["cell_sm"])],
        [Paragraph("可能结论 Probable", ST["cell"]),
         Paragraph(str(len(pc)), ST["cell"]),
         Paragraph(summarize_list(pc), ST["cell_sm"])],
        [Paragraph("争议要点 Contested", ST["cell"]),
         Paragraph(str(len(cp)), ST["cell"]),
         Paragraph(summarize_list(cp), ST["cell_sm"])],
    ]

    col_widths = [28 * mm, 16 * mm, CONTENT_W - 44 * mm]
    story.append(make_table(rows, col_widths))
    story.append(Spacer(1, 4 * mm))


def build_watchlist_table(story, final_report):
    """Section 4: 24小时监控清单 table."""
    watchlist = final_report.get("watchlist_24h", [])
    if not watchlist:
        return

    story.append(Paragraph("24小时监控清单 24h Watchlist", ST["h2"]))

    header = [
        Paragraph("<b>监控项 Item</b>", ST["cell_header"]),
        Paragraph("<b>逆转触发条件 Reversal Trigger</b>", ST["cell_header"]),
    ]
    rows = [header]
    for wl in watchlist:
        rows.append([
            Paragraph(esc(safe_str(wl.get("item", ""))), ST["cell"]),
            Paragraph(esc(safe_str(wl.get("reversal_trigger", ""))), ST["cell_sm"]),
        ])

    col_widths = [0.35 * CONTENT_W, 0.65 * CONTENT_W]
    story.append(make_table(rows, col_widths))
    story.append(Spacer(1, 4 * mm))


def build_overall_judgment(story, final_report):
    """Section 5: 总判断 highlighted box."""
    base_case = final_report.get("scenario_outlook", {}).get("base_case", "")
    verdict = final_report.get("verdict_summary", "")
    if not base_case and not verdict:
        return

    story.append(Paragraph("总判断 Overall Judgment", ST["h2"]))

    content = []
    if verdict:
        content.append(Paragraph(f"<b>{esc(verdict)}</b>", ST["highlight"]))
        content.append(Spacer(1, 2 * mm))
    if base_case:
        content.append(Paragraph(esc(base_case), ST["body"]))

    box = Table([[content]], colWidths=[CONTENT_W - 8 * mm])
    box.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), HexColor("#EFEBE9")),
        ("BOX", (0, 0), (-1, -1), 1.5, C_JUDGE),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(box)
    story.append(Spacer(1, 4 * mm))


def build_round_detail(story, round_num, pro, con, judge, is_first=True):
    """Per-round detail exchange table."""
    cn = CN_NUMS.get(round_num, str(round_num))

    if not is_first:
        story.append(Spacer(1, 4 * mm))

    story.append(Paragraph(f"第{cn}轮交锋 Round {round_num} Detail", ST["h2"]))

    # Legend
    legend_text = (
        '<font color="#B71C1C">[R]</font> = 被对方反驳 Rebutted &nbsp;&nbsp;'
        '<font color="#E65100">[J]</font> = 被裁判质疑 Questioned &nbsp;&nbsp;'
        '<font color="#212121">[X]</font> = 被事实推翻 Overturned'
    )
    story.append(Paragraph(legend_text, ST["legend"]))
    story.append(Spacer(1, 2 * mm))

    header = [
        Paragraph("<b>原始论点 Claim</b>", ST["cell_header"]),
        Paragraph("<b>谁的 Side</b>", ST["cell_header"]),
        Paragraph("<b>被谁打 Attacked</b>", ST["cell_header"]),
        Paragraph("<b>怎么打的 How</b>", ST["cell_header"]),
        Paragraph("<b>裁判怎么说 Judge Says</b>", ST["cell_header"]),
    ]
    rows = [header]

    # Collect all arguments from both sides
    all_args = []
    for arg in pro.get("arguments", []):
        all_args.append(("正方", arg, con, judge))
    for arg in con.get("arguments", []):
        all_args.append(("反方", arg, pro, judge))

    for side, arg, opponent, j in all_args:
        claim_id = arg.get("claim_id", "")
        claim_text = safe_str(arg.get("claim_text", ""))

        attackers = []
        attack_details = []
        judge_says = []

        # Opponent rebuttals targeting this claim
        for reb in opponent.get("rebuttals", []):
            target = reb.get("target_claim_id", "")
            if target == claim_id or _claim_matches(target, side, arg, pro, con):
                opp_label = "反方" if side == "正方" else "正方"
                attackers.append(red_marker(f"{opp_label}反驳"))
                attack_details.append(safe_str(reb.get("rebuttal_text", "")))

        # Judge causal validity flags
        for flag in j.get("causal_validity_flags", []):
            if flag.get("claim_id") == claim_id or _claim_matches(flag.get("claim_id", ""), side, arg, pro, con):
                sev = flag.get("severity", "")
                attackers.append(orange_marker(f"裁判质疑 {sev}"))
                attack_details.append(safe_str(flag.get("issue", "")))

        # Judge verification results
        for vr in j.get("verification_results", []):
            if vr.get("claim_id") == claim_id or _claim_matches(vr.get("claim_id", ""), side, arg, pro, con):
                status = vr.get("new_status", "")
                if status in ("contested", "stale"):
                    attackers.append(orange_marker(f"判定 {status}"))
                judge_says.append(safe_str(vr.get("reasoning", "")))

        attackers_text = "<br/>".join(attackers) if attackers else "—"
        details_text = "<br/>".join(esc(d) for d in attack_details) if attack_details else "—"
        judge_text = "<br/>".join(esc(j_text) for j_text in judge_says) if judge_says else "—"

        side_style = ST["cell_pro"] if side == "正方" else ST["cell_con"]

        rows.append([
            Paragraph(esc(claim_text), ST["cell_sm"]),
            Paragraph(side, side_style),
            Paragraph(attackers_text, ST["cell_sm"]),
            Paragraph(details_text, ST["cell_sm"]),
            Paragraph(judge_text, ST["cell_sm"]),
        ])

    col_widths = [
        0.20 * CONTENT_W,
        0.06 * CONTENT_W,
        0.14 * CONTENT_W,
        0.28 * CONTENT_W,
        0.32 * CONTENT_W,
    ]
    story.append(make_table(rows, col_widths))


def _claim_matches(target_id, side, arg, pro, con):
    """Match target_claim_id like 'clm_1_pro_1' to the right argument by index."""
    if not target_id:
        return False
    parts = target_id.split("_")
    if len(parts) < 4:
        return False
    try:
        target_side = parts[2].lower()
        target_idx = int(parts[3]) - 1
    except (ValueError, IndexError):
        return False

    side_lower = "pro" if side == "正方" else "con"
    if target_side != side_lower:
        return False

    source = pro if side == "正方" else con
    args = source.get("arguments", [])
    return 0 <= target_idx < len(args) and args[target_idx] is arg


# ═════════════════════════════════════════════════════════════
# Page template
# ═════════════════════════════════════════════════════════════

def add_page_decorations(canvas_obj, doc):
    """Add page number and thin lines."""
    canvas_obj.saveState()
    canvas_obj.setFont(FONT_NAME, 7)
    canvas_obj.setFillColor(C_MUTED)
    page = canvas_obj.getPageNumber()
    canvas_obj.drawCentredString(PAGE_W / 2, 12 * mm, f"Insight Debator | Page {page}")
    canvas_obj.setStrokeColor(C_DIVIDER)
    canvas_obj.setLineWidth(0.5)
    canvas_obj.line(20 * mm, PAGE_H - 15 * mm, PAGE_W - 20 * mm, PAGE_H - 15 * mm)
    canvas_obj.line(20 * mm, 18 * mm, PAGE_W - 20 * mm, 18 * mm)
    canvas_obj.restoreState()


# ═════════════════════════════════════════════════════════════
# Main
# ═════════════════════════════════════════════════════════════

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/generate_debate_pdf.py <workspace_path> [output_filename]")
        sys.exit(1)

    workspace = os.path.abspath(sys.argv[1])
    output_name = sys.argv[2] if len(sys.argv) > 2 else "executive_summary.pdf"

    if not os.path.isdir(workspace):
        print(f"Error: workspace not found: {workspace}")
        sys.exit(1)

    # Register CJK font
    if not register_fonts():
        print("Error: no CJK font found and download failed.")
        sys.exit(1)

    init_styles()

    # Load config
    config = load_json(os.path.join(workspace, "config.json"))
    round_count = config.get("round_count", detect_round_count(workspace))

    # Load round data
    rounds_data = []
    for r in range(1, round_count + 1):
        round_dir = os.path.join(workspace, f"rounds/round_{r}")
        pro = load_json(os.path.join(round_dir, "pro_turn.json"))
        con = load_json(os.path.join(round_dir, "con_turn.json"))
        judge = load_json(os.path.join(round_dir, "judge_ruling.json"))
        rounds_data.append((pro, con, judge))

    # Load final report
    final_report = load_json(os.path.join(workspace, "reports/final_report.json"))

    # Ensure output directory
    reports_dir = os.path.join(workspace, "reports")
    os.makedirs(reports_dir, exist_ok=True)
    output_path = os.path.join(reports_dir, output_name)

    # Build PDF
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=20 * mm, rightMargin=20 * mm,
        topMargin=22 * mm, bottomMargin=25 * mm,
        title=config.get("topic", "Debate Report"),
        author="Insight Debator",
    )

    story = []

    # Part 1: Executive Summary
    build_basic_info_table(story, config, final_report)
    build_round_overview_table(story, rounds_data)
    build_conclusions_table(story, final_report)
    build_watchlist_table(story, final_report)
    build_overall_judgment(story, final_report)

    # Part 2: Round Details
    story.append(PageBreak())
    for r, (pro, con, judge) in enumerate(rounds_data, 1):
        build_round_detail(story, r, pro, con, judge, is_first=(r == 1))

    doc.build(story, onFirstPage=add_page_decorations, onLaterPages=add_page_decorations)
    print(f"PDF generated: {output_path}")


if __name__ == "__main__":
    main()
