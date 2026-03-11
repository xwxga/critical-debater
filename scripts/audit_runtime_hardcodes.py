#!/usr/bin/env python3
"""
Fail-fast audit for hardcoded scenario residues in runtime generator paths.
"""

from __future__ import annotations

import re
from pathlib import Path

TARGETS = [
    Path("scripts/generate_debate_pdf.py"),
]

BANNED_PATTERNS = {
    r"Iran_Debate_Report": "legacy static output filename",
    r"\bIran\b": "legacy topic marker",
    r"伊朗": "legacy Chinese topic marker",
    r"March\s+9,\s*2026": "fixed historical generation date",
    r"2026年3月9日": "fixed historical Chinese date",
    r"range\(1,\s*4\)": "fixed round loop",
}


def scan_file(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    findings: list[str] = []
    for pattern, desc in BANNED_PATTERNS.items():
        for m in re.finditer(pattern, text):
            line = text.count("\n", 0, m.start()) + 1
            findings.append(f"{path}:{line}: {desc}: /{pattern}/")
    return findings


def main() -> int:
    all_findings: list[str] = []
    for t in TARGETS:
        if not t.exists():
            all_findings.append(f"{t}: missing target file")
            continue
        all_findings.extend(scan_file(t))

    if all_findings:
        print("Hardcode audit FAILED:")
        for f in all_findings:
            print(f"- {f}")
        return 1

    print("Hardcode audit PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
