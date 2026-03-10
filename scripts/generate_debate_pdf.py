#!/usr/bin/env python3
"""
Generate a beautiful bilingual PDF report of the Iran debate.
生成伊朗局势辩论的美观双语 PDF 报告。
"""

import json
import os

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, white
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak,
    Table, TableStyle, HRFlowable,
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# ── Paths ──
BASE = "/Users/wenxiangxu/Desktop/projects/insight-debator/debate-workspace"
SCRIPTS = "/Users/wenxiangxu/Desktop/projects/insight-debator/scripts"
OUTPUT = os.path.join(BASE, "reports/Iran_Debate_Report.pdf")

# ── Colors ──
C_PRO       = HexColor("#1B5E20")
C_PRO_BG    = HexColor("#E8F5E9")
C_CON       = HexColor("#B71C1C")
C_CON_BG    = HexColor("#FFEBEE")
C_JUDGE     = HexColor("#E65100")
C_JUDGE_BG  = HexColor("#FFF3E0")
C_TITLE     = HexColor("#1A237E")
C_SUBTITLE  = HexColor("#283593")
C_BODY      = HexColor("#212121")
C_MUTED     = HexColor("#616161")
C_ACCENT    = HexColor("#0D47A1")
C_DIVIDER   = HexColor("#BDBDBD")
C_COVER_BG  = HexColor("#0D1B2A")
C_GOLD      = HexColor("#FFB300")

# ── Register Fonts ──
pdfmetrics.registerFont(TTFont("ArialUnicode", "/Library/Fonts/Arial Unicode.ttf"))

# ── Load translations ──
with open(os.path.join(SCRIPTS, "translations.json"), "r", encoding="utf-8") as f:
    TR = json.load(f)


def esc(text):
    if not text:
        return ""
    return (text.replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;").replace("'", "&#39;"))


def make_divider():
    return HRFlowable(width="100%", thickness=0.5, color=C_DIVIDER,
                      spaceBefore=4*mm, spaceAfter=4*mm)


def make_colored_box(elements, bg_color, border_color):
    t = Table([[elements]], colWidths=[155*mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), bg_color),
        ("BOX", (0, 0), (-1, -1), 1, border_color),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    return t


def S(name, **overrides):
    """Create a ParagraphStyle with ArialUnicode as base."""
    defaults = {
        "fontName": "ArialUnicode", "fontSize": 10, "leading": 16,
        "textColor": C_BODY, "alignment": TA_LEFT, "spaceAfter": 3*mm,
    }
    defaults.update(overrides)
    return ParagraphStyle(name, **defaults)


# ── All styles ──
ST = {
    "cover_en": S("cover_en", fontSize=28, leading=36, alignment=TA_CENTER, textColor=white, spaceAfter=4*mm),
    "cover_zh": S("cover_zh", fontSize=22, leading=30, alignment=TA_CENTER, textColor=C_GOLD, spaceAfter=12*mm),
    "cover_sub": S("cover_sub", fontSize=13, leading=20, alignment=TA_CENTER, textColor=HexColor("#B0BEC5"), spaceAfter=3*mm),
    "cover_date": S("cover_date", fontSize=11, leading=16, alignment=TA_CENTER, textColor=HexColor("#78909C")),
    "h1": S("h1", fontSize=20, leading=28, textColor=C_TITLE, spaceAfter=6*mm, spaceBefore=8*mm),
    "h2": S("h2", fontSize=15, leading=22, textColor=C_SUBTITLE, spaceAfter=4*mm, spaceBefore=6*mm),
    "h3": S("h3", fontSize=12, leading=18, textColor=C_ACCENT, spaceAfter=3*mm, spaceBefore=4*mm),
    "body": S("body", alignment=TA_JUSTIFY),
    "body_zh": S("body_zh", textColor=C_MUTED, spaceAfter=4*mm, alignment=TA_JUSTIFY),
    "body_sm": S("body_sm", fontSize=9, leading=14, spaceAfter=2*mm, alignment=TA_JUSTIFY),
    "body_sm_zh": S("body_sm_zh", fontSize=9, leading=14, textColor=C_MUTED, spaceAfter=3*mm, alignment=TA_JUSTIFY),
    "pro_h": S("pro_h", fontSize=13, leading=20, textColor=C_PRO, spaceAfter=3*mm, spaceBefore=5*mm),
    "con_h": S("con_h", fontSize=13, leading=20, textColor=C_CON, spaceAfter=3*mm, spaceBefore=5*mm),
    "judge_h": S("judge_h", fontSize=13, leading=20, textColor=C_JUDGE, spaceAfter=3*mm, spaceBefore=5*mm),
    "rc_label": S("rc_label", fontSize=9, leading=13, textColor=C_ACCENT, spaceAfter=1*mm, leftIndent=8*mm),
    "rc_text": S("rc_text", fontSize=9, leading=14, textColor=C_MUTED, spaceAfter=2*mm, leftIndent=12*mm, alignment=TA_JUSTIFY),
    "rc_text_zh": S("rc_text_zh", fontSize=9, leading=14, textColor=HexColor("#9E9E9E"), spaceAfter=3*mm, leftIndent=12*mm, alignment=TA_JUSTIFY),
    "rebuttal": S("rebuttal", fontSize=9.5, leading=15, textColor=HexColor("#4A148C"), spaceAfter=2*mm, leftIndent=8*mm, alignment=TA_JUSTIFY),
    "rebuttal_zh": S("rebuttal_zh", fontSize=9.5, leading=15, textColor=HexColor("#7B1FA2"), spaceAfter=3*mm, leftIndent=8*mm, alignment=TA_JUSTIFY),
    "verified": S("verified", fontSize=9.5, leading=15, textColor=C_PRO, spaceAfter=2*mm, leftIndent=8*mm),
    "contested": S("contested", fontSize=9.5, leading=15, textColor=C_JUDGE, spaceAfter=2*mm, leftIndent=8*mm),
}


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def bilingual(en_text, zh_text, en_style, zh_style, story):
    story.append(Paragraph(esc(en_text), en_style))
    if zh_text:
        story.append(Paragraph(esc(zh_text), zh_style))


# ═════════════════════════════════════════════════════════════
# Cover
# ═════════════════════════════════════════════════════════════
def build_cover(story):
    story.append(Spacer(1, 50*mm))
    rows = [
        Paragraph("INSIGHT DEBATOR", ST["cover_en"]),
        Paragraph("Multi-Agent Debate Analysis Report", ST["cover_sub"]),
        Paragraph("多智能体辩论分析报告", ST["cover_sub"]),
        Spacer(1, 10*mm),
        HRFlowable(width="60%", thickness=1.5, color=C_GOLD, spaceBefore=2*mm, spaceAfter=6*mm),
        Paragraph("Will the Iran Situation Escalate Next Week?", ST["cover_en"]),
        Paragraph("下周伊朗局势是否会升级？", ST["cover_zh"]),
        Spacer(1, 15*mm),
        Paragraph("3-Round Structured Debate with Independent Verification", ST["cover_sub"]),
        Paragraph("三轮结构化辩论 + 独立验证", ST["cover_sub"]),
        Spacer(1, 8*mm),
        Paragraph("Generated: March 9, 2026 | 生成：2026年3月9日", ST["cover_date"]),
        Paragraph("Pro (Sonnet) vs Con (Sonnet) | Judge (Opus)", ST["cover_date"]),
    ]
    t = Table([[r] for r in rows], colWidths=[170*mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), C_COVER_BG),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("LEFTPADDING", (0, 0), (-1, -1), 15),
        ("RIGHTPADDING", (0, 0), (-1, -1), 15),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
    ]))
    story.append(t)
    story.append(PageBreak())


# ═════════════════════════════════════════════════════════════
# TOC
# ═════════════════════════════════════════════════════════════
def build_toc(story):
    story.append(Paragraph("Table of Contents / 目录", ST["h1"]))
    story.append(Spacer(1, 4*mm))
    items = [
        ("1. Executive Summary / 执行摘要", "核心发现概览"),
        ("2. Round 1 / 第一轮", "开场论点 + 裁判裁定"),
        ("3. Round 2 / 第二轮", "代理人升级 + 外交渠道"),
        ("4. Round 3 / 第三轮", "战争目标 + 指挥权"),
        ("5. Final Report / 最终报告", "已验证事实、结论、监控清单"),
        ("6. Scenario Outlook / 情景展望", "基线情景 + 触发因素"),
    ]
    for title, desc in items:
        story.append(Paragraph(f"<b>{esc(title)}</b>", ST["body"]))
        story.append(Paragraph(f"<i>{esc(desc)}</i>", ST["body_zh"]))
    story.append(PageBreak())


# ═════════════════════════════════════════════════════════════
# Executive Summary
# ═════════════════════════════════════════════════════════════
def build_exec_summary(story, fr):
    story.append(Paragraph("1. Executive Summary / 执行摘要", ST["h1"]))
    story.append(make_divider())

    data = [
        ["指标 / Metric", "数值 / Value"],
        ["辩论主题 / Topic", "下周伊朗局势是否会升级？\nWill the Iran situation escalate next week?"],
        ["总轮数 / Rounds", "3"],
        ["已验证事实 / Verified Facts", str(len(fr.get("verified_facts", [])))],
        ["可能结论 / Probable Conclusions", str(len(fr.get("probable_conclusions", [])))],
        ["争议要点 / Contested Points", str(len(fr.get("contested_points", [])))],
        ["监控清单 / Watchlist", str(len(fr.get("watchlist_24h", [])))],
    ]
    t = Table(data, colWidths=[80*mm, 80*mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), C_ACCENT),
        ("TEXTCOLOR", (0, 0), (-1, 0), white),
        ("FONTNAME", (0, 0), (-1, -1), "ArialUnicode"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("LEADING", (0, 0), (-1, -1), 15),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, C_DIVIDER),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [white, HexColor("#F5F5F5")]),
    ]))
    story.append(t)
    story.append(Spacer(1, 6*mm))

    story.append(Paragraph("基线评估 / Base Case Assessment", ST["h2"]))
    bc = fr.get("scenario_outlook", {}).get("base_case", "")
    if " / " in bc:
        en, zh = bc.split(" / ", 1)
        bilingual(en, zh, ST["body"], ST["body_zh"], story)
    else:
        story.append(Paragraph(esc(bc), ST["body"]))
    story.append(PageBreak())


# ═════════════════════════════════════════════════════════════
# Argument builder
# ═════════════════════════════════════════════════════════════
def build_argument(story, arg, idx, side, round_num):
    color = C_PRO if side == "pro" else C_CON
    bg = C_PRO_BG if side == "pro" else C_CON_BG
    icon = "正方 PRO" if side == "pro" else "反方 CON"
    h_style = ST["pro_h"] if side == "pro" else ST["con_h"]

    story.append(Paragraph(f"<b>[{icon}] 论点 {idx} / Argument {idx}</b>", h_style))

    # Claim: EN
    en_claim = arg["claim_text"]
    # Claim: ZH from translations
    tr_key = f"R{round_num}_{side.upper()}_{idx}"
    zh_claim = TR["claims"].get(tr_key, "")

    claim_ps = S("claim_inner", fontSize=10.5, leading=16, textColor=color, alignment=TA_JUSTIFY)
    claim_ps_zh = S("claim_inner_zh", fontSize=10, leading=15, textColor=HexColor("#424242"), alignment=TA_JUSTIFY)

    inner = [Paragraph(f"<b>{esc(en_claim)}</b>", claim_ps)]
    if zh_claim:
        inner.append(Spacer(1, 2*mm))
        inner.append(Paragraph(esc(zh_claim), claim_ps_zh))
    story.append(make_colored_box(inner, bg, color))
    story.append(Spacer(1, 2*mm))

    # Reasoning chain
    rc = arg.get("reasoning_chain", {})
    tr_rc = TR["reasoning_chains"].get(tr_key, {})

    labels = [
        ("observed_facts", "观察到的事实 / Observed Facts"),
        ("mechanism", "机制 / Mechanism"),
        ("scenario_implication", "情景推演 / Scenario Implication"),
        ("trigger_conditions", "触发条件 / Trigger Conditions"),
        ("falsification_conditions", "证伪条件 / Falsification Conditions"),
    ]
    for key, label in labels:
        en_text = rc.get(key, "")
        zh_text = tr_rc.get(key, "")
        if en_text:
            story.append(Paragraph(f"<b>{esc(label)}</b>", ST["rc_label"]))
            story.append(Paragraph(esc(en_text), ST["rc_text"]))
            if zh_text:
                story.append(Paragraph(esc(zh_text), ST["rc_text_zh"]))

    story.append(Spacer(1, 2*mm))


def build_rebuttal(story, reb, side, round_num, reb_idx):
    icon = "正方 PRO" if side == "pro" else "反方 CON"

    story.append(Paragraph(
        f"<b>[{icon}] 反驳 / Rebuttal</b> (针对 {esc(reb.get('target_claim_id', ''))})",
        ST["rc_label"]
    ))

    # EN
    story.append(Paragraph(esc(reb.get("rebuttal_text", "")), ST["rebuttal"]))

    # ZH
    tr_key = f"R{round_num}_{side.upper()}_reb_{reb_idx}"
    zh = TR["rebuttals"].get(tr_key, "")
    if zh:
        story.append(Paragraph(esc(zh), ST["rebuttal_zh"]))


# ═════════════════════════════════════════════════════════════
# Round builder
# ═════════════════════════════════════════════════════════════
def build_round(story, rnd, pro, con, judge):
    cn_num = {1: "一", 2: "二", 3: "三"}[rnd]
    story.append(Paragraph(f"Round {rnd} / 第{cn_num}轮", ST["h1"]))
    story.append(make_divider())

    # ── PRO ──
    story.append(Paragraph(
        "<font color='#1B5E20'>&#9654;</font> <b>正方 Pro Side (Sonnet)</b>",
        ST["pro_h"]
    ))
    story.append(Paragraph(
        "<i>立场：局势将会升级 / Position: The situation WILL escalate</i>",
        ST["body_zh"]
    ))

    for i, arg in enumerate(pro.get("arguments", []), 1):
        build_argument(story, arg, i, "pro", rnd)

    for i, reb in enumerate(pro.get("rebuttals", []), 1):
        build_rebuttal(story, reb, "pro", rnd, i)

    for mr in pro.get("mandatory_responses", []):
        if mr.get("response_text"):
            story.append(Paragraph(
                f"<b>[正方] 必答回应 / Response to {esc(mr.get('point_id', ''))}</b>",
                ST["rc_label"]
            ))
            story.append(Paragraph(esc(mr["response_text"]), ST["rc_text"]))

    story.append(make_divider())

    # ── CON ──
    story.append(Paragraph(
        "<font color='#B71C1C'>&#9654;</font> <b>反方 Con Side (Sonnet)</b>",
        ST["con_h"]
    ))
    story.append(Paragraph(
        "<i>立场：局势不会升级 / Position: The situation will NOT escalate</i>",
        ST["body_zh"]
    ))

    for i, arg in enumerate(con.get("arguments", []), 1):
        build_argument(story, arg, i, "con", rnd)

    for i, reb in enumerate(con.get("rebuttals", []), 1):
        build_rebuttal(story, reb, "con", rnd, i)

    for mr in con.get("mandatory_responses", []):
        if mr.get("response_text"):
            story.append(Paragraph(
                f"<b>[反方] 必答回应 / Response to {esc(mr.get('point_id', ''))}</b>",
                ST["rc_label"]
            ))
            story.append(Paragraph(esc(mr["response_text"]), ST["rc_text"]))

    story.append(make_divider())

    # ── JUDGE ──
    story.append(Paragraph(
        "<font color='#E65100'>&#9654;</font> <b>裁判裁定 / Judge Ruling (Opus)</b>",
        ST["judge_h"]
    ))

    # Verification results
    story.append(Paragraph("<b>验证结果 / Verification Results</b>", ST["h3"]))

    for vr in judge.get("verification_results", []):
        status = vr.get("new_status", "unverified")
        cid = vr.get("claim_id", "")
        status_map = {
            "verified": ("&#10004;", "#1B5E20", "已验证 VERIFIED"),
            "contested": ("&#9888;", "#E65100", "有争议 CONTESTED"),
            "stale": ("&#10060;", "#616161", "已过期 STALE"),
        }
        icon, color, label = status_map.get(status, ("?", "#616161", status))
        s = ST["verified"] if status == "verified" else ST["contested"]

        story.append(Paragraph(
            f"<b><font color='{color}'>{icon} [{esc(cid)}] {label}</font></b>", s
        ))
        # EN reasoning
        story.append(Paragraph(esc(vr.get("reasoning", "")), ST["rc_text"]))

        # ZH reasoning from translations
        v_idx = list(judge.get("verification_results", [])).index(vr) + 1
        tr_key = f"R{rnd}_V{v_idx}"
        zh_v = TR["judge_verifications"].get(tr_key, "")
        if zh_v:
            story.append(Paragraph(esc(zh_v), ST["rc_text_zh"]))

    # Causal validity flags
    flags = judge.get("causal_validity_flags", [])
    if flags:
        story.append(Paragraph("<b>因果有效性问题 / Causal Validity Issues</b>", ST["h3"]))
        for i, flag in enumerate(flags, 1):
            sev = flag.get("severity", "minor")
            sev_color = {"critical": "#B71C1C", "moderate": "#E65100", "minor": "#616161"}.get(sev, "#616161")
            story.append(Paragraph(
                f"<font color='{sev_color}'><b>[{esc(flag.get('claim_id', ''))}] 严重度: {sev.upper()}</b></font>",
                ST["rc_label"]
            ))
            story.append(Paragraph(esc(flag.get("issue", "")), ST["rc_text"]))
            tr_key = f"R{rnd}_F{i}"
            zh_f = TR["judge_causal_flags"].get(tr_key, "")
            if zh_f:
                story.append(Paragraph(esc(zh_f), ST["rc_text_zh"]))

    # Mandatory response points
    mrps = judge.get("mandatory_response_points", [])
    if mrps:
        story.append(Paragraph("<b>必答要点 / Mandatory Response Points</b>", ST["h3"]))
        for i, mrp in enumerate(mrps, 1):
            target = mrp.get("target", "both")
            t_map = {"pro": ("正方", "#1B5E20"), "con": ("反方", "#B71C1C"), "both": ("双方", "#0D47A1")}
            t_label, t_color = t_map.get(target, ("both", "#0D47A1"))
            pid = mrp.get("point_id", "")

            story.append(Paragraph(
                f"<font color='{t_color}'><b>[{esc(pid)}] 针对: {t_label} {target.upper()}</b></font>",
                ST["rc_label"]
            ))
            story.append(Paragraph(esc(mrp.get("point", "")), ST["rc_text"]))
            tr_key = f"R{rnd}_MRP_{i}"
            zh_mrp = TR["judge_mrps"].get(tr_key, "")
            if zh_mrp:
                story.append(Paragraph(esc(zh_mrp), ST["rc_text_zh"]))

            reason = mrp.get("reason", "")
            if reason:
                story.append(Paragraph(f"<i>Reason: {esc(reason)}</i>", ST["rc_text"]))
                tr_reason_key = f"R{rnd}_MRP_{i}_reason"
                zh_r = TR["judge_mrps"].get(tr_reason_key, "")
                if zh_r:
                    story.append(Paragraph(f"<i>{esc(zh_r)}</i>", ST["rc_text_zh"]))

    # Round summary
    summary_en = judge.get("round_summary", "")
    tr_sum_key = f"R{rnd}"
    summary_zh = TR["round_summaries"].get(tr_sum_key, "")

    if summary_en:
        story.append(Paragraph("<b>回合总结 / Round Summary</b>", ST["h3"]))
        inner = [
            Paragraph(esc(summary_en), S("sum_en", fontSize=10, leading=16, textColor=C_BODY, alignment=TA_JUSTIFY)),
        ]
        if summary_zh:
            inner.append(Spacer(1, 3*mm))
            inner.append(Paragraph(esc(summary_zh), S("sum_zh", fontSize=10, leading=16, textColor=C_MUTED, alignment=TA_JUSTIFY)))
        story.append(make_colored_box(inner, C_JUDGE_BG, C_JUDGE))

    story.append(PageBreak())


# ═════════════════════════════════════════════════════════════
# Final Report
# ═════════════════════════════════════════════════════════════
def build_bilingual_list(story, items, h_en, h_zh, icon, icon_color):
    story.append(Paragraph(
        f"<font color='{icon_color}'>{icon}</font> <b>{h_zh} / {h_en}</b> ({len(items)} items)",
        ST["h2"]
    ))
    for i, item in enumerate(items, 1):
        if " / " in item:
            en, zh = item.split(" / ", 1)
            story.append(Paragraph(f"<b>{i}.</b> {esc(en)}", ST["body_sm"]))
            story.append(Paragraph(esc(zh), ST["body_sm_zh"]))
        else:
            story.append(Paragraph(f"<b>{i}.</b> {esc(item)}", ST["body_sm"]))


def build_final_report(story, fr):
    story.append(Paragraph("5. 最终报告 / Final Report", ST["h1"]))
    story.append(make_divider())

    build_bilingual_list(story, fr.get("verified_facts", []),
                         "Verified Facts", "已验证事实", "&#10004;", "#1B5E20")
    story.append(make_divider())

    build_bilingual_list(story, fr.get("probable_conclusions", []),
                         "Probable Conclusions", "可能结论", "&#9654;", "#0D47A1")
    story.append(make_divider())

    build_bilingual_list(story, fr.get("contested_points", []),
                         "Contested Points", "争议要点", "&#9888;", "#E65100")
    story.append(make_divider())

    build_bilingual_list(story, fr.get("to_verify", []),
                         "Items to Verify", "待验证事项", "&#10067;", "#616161")

    story.append(PageBreak())


# ═════════════════════════════════════════════════════════════
# Scenario Outlook
# ═════════════════════════════════════════════════════════════
def build_scenario(story, fr):
    story.append(Paragraph("6. 情景展望 / Scenario Outlook", ST["h1"]))
    story.append(make_divider())

    outlook = fr.get("scenario_outlook", {})

    story.append(Paragraph("<b>基线情景 / Base Case</b>", ST["h2"]))
    bc = outlook.get("base_case", "")
    if " / " in bc:
        en, zh = bc.split(" / ", 1)
        bilingual(en, zh, ST["body"], ST["body_zh"], story)
    else:
        story.append(Paragraph(esc(bc), ST["body"]))

    def build_trigger_list(title_zh, title_en, triggers, icon, icon_color):
        story.append(Paragraph(
            f"<font color='{icon_color}'>{icon}</font> <b>{title_zh} / {title_en}</b>",
            ST["h2"]
        ))
        for tr in triggers:
            if " / " in tr:
                en, zh = tr.split(" / ", 1)
                story.append(Paragraph(f"&#8226; {esc(en)}", ST["body_sm"]))
                story.append(Paragraph(esc(zh), ST["body_sm_zh"]))
            else:
                story.append(Paragraph(f"&#8226; {esc(tr)}", ST["body_sm"]))

    build_trigger_list("降级触发因素", "Upside Triggers (De-escalation)",
                       outlook.get("upside_triggers", []), "&#9650;", "#1B5E20")
    build_trigger_list("升级触发因素", "Downside Triggers (Escalation)",
                       outlook.get("downside_triggers", []), "&#9660;", "#B71C1C")
    build_trigger_list("证伪条件", "Falsification Conditions",
                       outlook.get("falsification_conditions", []), "&#10060;", "#616161")

    story.append(make_divider())

    # Watchlist
    story.append(Paragraph(
        "<font color='#E65100'>&#9888;</font> <b>24小时监控清单 / 24-Hour Watchlist</b>",
        ST["h2"]
    ))

    for i, wl in enumerate(fr.get("watchlist_24h", []), 1):
        item_text = wl.get("item", "")
        reversal = wl.get("reversal_trigger", "")
        source = wl.get("monitoring_source", "")

        if " / " in item_text:
            en, zh = item_text.split(" / ", 1)
            story.append(Paragraph(f"<b>{i}. {esc(en)}</b>", ST["body"]))
            story.append(Paragraph(esc(zh), ST["body_zh"]))
        else:
            story.append(Paragraph(f"<b>{i}. {esc(item_text)}</b>", ST["body"]))

        if reversal:
            if " / " in reversal:
                en, zh = reversal.split(" / ", 1)
                story.append(Paragraph(f"<font color='#B71C1C'><b>逆转触发:</b></font> {esc(en)}", ST["rc_text"]))
                story.append(Paragraph(esc(zh), ST["rc_text_zh"]))
            else:
                story.append(Paragraph(f"<font color='#B71C1C'><b>逆转触发:</b></font> {esc(reversal)}", ST["rc_text"]))

        if source:
            story.append(Paragraph(f"<font color='#0D47A1'><b>监控来源:</b></font> {esc(source)}", ST["rc_text"]))

        story.append(Spacer(1, 2*mm))


# ═════════════════════════════════════════════════════════════
# Closing page
# ═════════════════════════════════════════════════════════════
def build_closing(story):
    story.append(PageBreak())
    story.append(Spacer(1, 60*mm))
    rows = [
        Paragraph("报告结束 / End of Report", ST["cover_en"]),
        Spacer(1, 6*mm),
        Paragraph("Generated by Insight Debator Multi-Agent System", ST["cover_sub"]),
        Paragraph("由 Insight Debator 多智能体系统生成", ST["cover_sub"]),
        Spacer(1, 6*mm),
        Paragraph("正方 Pro: Claude Sonnet | 反方 Con: Claude Sonnet | 裁判 Judge: Claude Opus", ST["cover_date"]),
        Paragraph("编排 Orchestrator: Claude Sonnet | 基础设施 Infrastructure: Claude Code", ST["cover_date"]),
        Spacer(1, 6*mm),
        Paragraph("本报告反映截至2026年3月9日的信息状态。", ST["cover_date"]),
        Paragraph("This report reflects information as of March 9, 2026.", ST["cover_date"]),
    ]
    t = Table([[r] for r in rows], colWidths=[170*mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), C_COVER_BG),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("LEFTPADDING", (0, 0), (-1, -1), 15),
        ("RIGHTPADDING", (0, 0), (-1, -1), 15),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
    ]))
    story.append(t)


# ═════════════════════════════════════════════════════════════
# Page template
# ═════════════════════════════════════════════════════════════
def add_page_number(canvas_obj, doc):
    canvas_obj.saveState()
    canvas_obj.setFont("ArialUnicode", 8)
    canvas_obj.setFillColor(C_MUTED)
    page = canvas_obj.getPageNumber()
    canvas_obj.drawCentredString(A4[0] / 2, 15*mm, f"Insight Debator | 伊朗局势分析 | 第 {page} 页")
    canvas_obj.setStrokeColor(C_DIVIDER)
    canvas_obj.setLineWidth(0.5)
    canvas_obj.line(20*mm, A4[1] - 15*mm, A4[0] - 20*mm, A4[1] - 15*mm)
    canvas_obj.line(20*mm, 20*mm, A4[0] - 20*mm, 20*mm)
    canvas_obj.restoreState()


# ═════════════════════════════════════════════════════════════
# Main
# ═════════════════════════════════════════════════════════════
def main():
    rounds = []
    for r in range(1, 4):
        pro = load_json(os.path.join(BASE, f"rounds/round_{r}/pro_turn.json"))
        con = load_json(os.path.join(BASE, f"rounds/round_{r}/con_turn.json"))
        judge = load_json(os.path.join(BASE, f"rounds/round_{r}/judge_ruling.json"))
        rounds.append((pro, con, judge))

    fr = load_json(os.path.join(BASE, "reports/final_report.json"))

    doc = SimpleDocTemplate(
        OUTPUT, pagesize=A4,
        leftMargin=20*mm, rightMargin=20*mm,
        topMargin=22*mm, bottomMargin=25*mm,
        title="Insight Debator: 伊朗局势分析",
        author="Insight Debator Multi-Agent System",
    )

    story = []
    build_cover(story)
    build_toc(story)
    build_exec_summary(story, fr)

    for i, (pro, con, judge) in enumerate(rounds, 1):
        build_round(story, i, pro, con, judge)

    build_final_report(story, fr)
    build_scenario(story, fr)
    build_closing(story)

    doc.build(story, onFirstPage=add_page_number, onLaterPages=add_page_number)
    print(f"PDF generated: {OUTPUT}")


if __name__ == "__main__":
    main()
