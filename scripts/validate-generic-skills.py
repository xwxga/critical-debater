#!/usr/bin/env python3
"""Validation gate for generic skills migration."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

EXPECTED_SKILLS = {
    "analogy-safeguard",
    "claim-ledger-update",
    "debate",
    "debate-turn",
    "evidence-verify",
    "final-synthesis",
    "freshness-check",
    "judge-audit",
    "source-ingest",
}

BANNED_PATTERNS = [
    re.compile(r"\bWebSearch\b"),
    re.compile(r"\bWebFetch\b"),
    re.compile(r"\bAgent tool\b", re.IGNORECASE),
    re.compile(r"\bopenclaw\b", re.IGNORECASE),
    re.compile(r"^version:\s*", re.MULTILINE),
    re.compile(r"^license:\s*", re.MULTILINE),
    re.compile(r"^metadata:\s*", re.MULTILINE),
]


def split_frontmatter(text: str) -> tuple[str, str]:
    if not text.startswith("---\n"):
        raise ValueError("missing frontmatter opening delimiter")
    end = text.find("\n---\n", 4)
    if end == -1:
        raise ValueError("missing frontmatter closing delimiter")
    return text[4:end], text[end + 5 :]


def top_level_keys(frontmatter: str) -> list[str]:
    keys: list[str] = []
    for line in frontmatter.splitlines():
        if re.match(r"^[A-Za-z0-9_-]+:\s*", line):
            keys.append(line.split(":", 1)[0])
    return keys


def validate_skill_file(path: Path, expected_name: str) -> list[str]:
    errors: list[str] = []
    text = path.read_text(encoding="utf-8")

    try:
        frontmatter, body = split_frontmatter(text)
    except ValueError as exc:
        return [f"{path}: {exc}"]

    keys = top_level_keys(frontmatter)
    if keys != ["name", "description"]:
        errors.append(f"{path}: frontmatter keys must be exactly ['name', 'description'], got {keys}")

    match_name = re.search(r"^name:\s*(.+?)\s*$", frontmatter, re.MULTILINE)
    if not match_name:
        errors.append(f"{path}: missing name field")
    elif match_name.group(1).strip() != expected_name:
        errors.append(f"{path}: name mismatch, expected '{expected_name}', got '{match_name.group(1).strip()}'")

    if "description:" not in frontmatter:
        errors.append(f"{path}: missing description field")

    if "## Runtime Capability Contract / 运行时能力契约" not in body:
        errors.append(f"{path}: missing runtime capability contract section")

    if "../_shared/references/capability-adapter.md" not in body:
        errors.append(f"{path}: missing capability-adapter shared reference")

    if "../_shared/references/execution-envelope.md" not in body:
        errors.append(f"{path}: missing execution-envelope shared reference")

    for pattern in BANNED_PATTERNS:
        if pattern.search(text):
            errors.append(f"{path}: banned provider-specific pattern found: {pattern.pattern}")

    return errors


def validate_claude_unchanged(repo_root: Path, base_ref: str | None = None) -> list[str]:
    if base_ref:
        verify = subprocess.run(
            ["git", "rev-parse", "--verify", base_ref],
            cwd=repo_root,
            text=True,
            capture_output=True,
            check=False,
        )
        if verify.returncode != 0:
            return [f"invalid --claude-diff-base ref '{base_ref}': {verify.stderr.strip()}"]

        proc = subprocess.run(
            ["git", "diff", "--name-only", f"{base_ref}...HEAD", "--", ".claude"],
            cwd=repo_root,
            text=True,
            capture_output=True,
            check=False,
        )
        if proc.returncode != 0:
            return [f"git diff command failed: {proc.stderr.strip()}"]

        changed = [line.strip() for line in proc.stdout.splitlines() if line.strip()]
        if changed:
            return [f".claude tree changed vs base '{base_ref}':"] + [f"  - {item}" for item in changed]
        return []

    proc = subprocess.run(
        ["git", "diff", "--name-only", "--", ".claude"],
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        return [f"git diff command failed: {proc.stderr.strip()}"]

    changed = [line.strip() for line in proc.stdout.splitlines() if line.strip()]
    if changed:
        return [".claude tree changed unexpectedly (working tree diff mode):"] + [f"  - {item}" for item in changed]
    return []


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate migrated generic skills")
    parser.add_argument(
        "--root",
        default=".agents/skills",
        help="Generic skills root directory (default: .agents/skills)",
    )
    parser.add_argument(
        "--check-claude-unchanged",
        action="store_true",
        help="Fail if .claude changed (default: working tree diff; use --claude-diff-base for PR-style diff)",
    )
    parser.add_argument(
        "--claude-diff-base",
        default=None,
        help="Optional git base ref for .claude diff check (example: origin/main). Uses <base>...HEAD.",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    root = (repo_root / args.root).resolve()

    if not root.exists():
        print(f"ERROR: generic skills root not found: {root}", file=sys.stderr)
        return 1

    errors: list[str] = []

    discovered = {
        p.name
        for p in root.iterdir()
        if p.is_dir() and p.name != "_shared"
    }

    missing = sorted(EXPECTED_SKILLS - discovered)
    extra = sorted(discovered - EXPECTED_SKILLS)

    if missing:
        errors.append(f"Missing expected generic skills: {missing}")
    if extra:
        errors.append(f"Unexpected extra skill directories: {extra}")

    for skill in sorted(EXPECTED_SKILLS):
        skill_file = root / skill / "SKILL.md"
        if not skill_file.exists():
            errors.append(f"Missing SKILL.md: {skill_file}")
            continue
        errors.extend(validate_skill_file(skill_file, skill))

    shared_contract = root / "_shared" / "references" / "data-contracts.md"
    shared_adapter = root / "_shared" / "references" / "capability-adapter.md"
    shared_envelope = root / "_shared" / "references" / "execution-envelope.md"

    for path in (shared_contract, shared_adapter, shared_envelope):
        if not path.exists():
            errors.append(f"Missing shared file: {path}")

    if args.check_claude_unchanged:
        errors.extend(validate_claude_unchanged(repo_root, args.claude_diff_base))

    if errors:
        print("FAILED generic skills validation:", file=sys.stderr)
        for err in errors:
            print(f"- {err}", file=sys.stderr)
        return 1

    print("OK: generic skills validation passed")
    print(f"- skills: {len(EXPECTED_SKILLS)}")
    print("- frontmatter keys: name + description only")
    print("- shared adapter docs: present")
    if args.check_claude_unchanged:
        if args.claude_diff_base:
            print(f"- .claude tree: unchanged vs {args.claude_diff_base}")
        else:
            print("- .claude tree: unchanged (working tree diff mode)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
