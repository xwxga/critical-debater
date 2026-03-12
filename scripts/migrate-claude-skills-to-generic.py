#!/usr/bin/env python3
"""Migrate .claude skills into generic .agents skills.

This script keeps trigger semantics while removing provider-specific bindings:
- frontmatter reduced to name + description
- WebSearch/WebFetch/Agent tool names rewritten to generic capability names
- shared data-contract reference moved under .agents/skills/_shared/references
"""

from __future__ import annotations

import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = ROOT / ".claude" / "skills"
DST_ROOT = ROOT / ".agents" / "skills"

SKILLS = [
    "analogy-safeguard",
    "claim-ledger-update",
    "debate",
    "debate-turn",
    "evidence-verify",
    "final-synthesis",
    "freshness-check",
    "judge-audit",
    "source-ingest",
]

REPLACEMENTS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\bWebSearch/WebFetch\b"), "`search`/`fetch` capabilities"),
    (re.compile(r"\bWebSearch\b"), "`search` capability"),
    (re.compile(r"\bWebFetch\b"), "`fetch` capability"),
    (re.compile(r"\bAgent tool\b", re.IGNORECASE), "`spawn_role` capability"),
    (re.compile(r"\bPlaywright MCP fallback\b"), "adapter-backed browser fallback"),
    (re.compile(r"\bMCP fallback\b"), "adapter fallback"),
    (
        re.compile(r"\.claude/skills/source-ingest/references/data-contracts\.md"),
        ".agents/skills/_shared/references/data-contracts.md",
    ),
    (
        re.compile(r"`references/data-contracts\.md`"),
        "`../_shared/references/data-contracts.md`",
    ),
    (
        re.compile(r"(?<!\.\./_shared/)references/data-contracts\.md"),
        "../_shared/references/data-contracts.md",
    ),
]

RUNTIME_SECTION = """
## Runtime Capability Contract / 运行时能力契约

Use the shared generic capability contract:

- `../_shared/references/capability-adapter.md`
- `../_shared/references/execution-envelope.md`

Tool names in this skill are capability-level and provider-agnostic:
- `search`
- `fetch`
- `spawn_role`
- `validate_json`
- `append_audit`

Fallback policy:
- `search`: native -> adapter -> `evidence_gap` soft-failure with audit note
- `fetch`: native -> adapter -> `fetch_skipped` soft-failure with audit note
- `spawn_role`: native -> adapter -> serial role emulation (`pro -> con -> judge`)

Model policy:
- Use tier names only: `fast`, `balanced`, `deep`
- Map provider-specific model names to these tiers at runtime
""".strip()


def split_frontmatter(text: str) -> tuple[str, str]:
    if not text.startswith("---\n"):
        raise ValueError("missing frontmatter opening delimiter")
    end = text.find("\n---\n", 4)
    if end == -1:
        raise ValueError("missing frontmatter closing delimiter")
    frontmatter = text[4:end]
    body = text[end + 5 :]
    return frontmatter, body


def extract_name_and_description(frontmatter: str) -> tuple[str, list[str]]:
    lines = frontmatter.splitlines()
    name: str | None = None
    desc_lines: list[str] = []

    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("name:"):
            name = line.split(":", 1)[1].strip()
        if line.startswith("description:"):
            desc_lines.append(line)
            i += 1
            while i < len(lines):
                nxt = lines[i]
                if re.match(r"^[A-Za-z0-9_-]+:\s*", nxt):
                    break
                desc_lines.append(nxt)
                i += 1
            break
        i += 1

    if not name or not desc_lines:
        raise ValueError("frontmatter missing required name or description")
    return name, desc_lines


def normalize_body(body: str) -> str:
    out = body
    for pattern, replacement in REPLACEMENTS:
        out = pattern.sub(replacement, out)
    out = out.replace(
        "../_shared/../_shared/references/data-contracts.md",
        "../_shared/references/data-contracts.md",
    )
    out = out.replace(
        ".agents/skills/_shared/../_shared/references/data-contracts.md",
        ".agents/skills/_shared/references/data-contracts.md",
    )

    if "## Runtime Capability Contract / 运行时能力契约" not in out:
        marker = "## When to Use / 何时使用"
        if marker in out:
            out = out.replace(marker, f"{RUNTIME_SECTION}\n\n{marker}", 1)
        else:
            out = f"{RUNTIME_SECTION}\n\n{out.lstrip()}"

    return out


def render_frontmatter(name: str, desc_lines: list[str]) -> str:
    if desc_lines[0].strip() == "description:":
        desc_lines[0] = "description: >"
    return "---\n" + f"name: {name}\n" + "\n".join(desc_lines) + "\n---\n"


def migrate_skill(skill_name: str) -> None:
    src = SRC_ROOT / skill_name / "SKILL.md"
    dst = DST_ROOT / skill_name / "SKILL.md"
    if not src.exists():
        raise FileNotFoundError(f"missing source skill: {src}")

    text = src.read_text(encoding="utf-8")
    frontmatter, body = split_frontmatter(text)
    name, desc_lines = extract_name_and_description(frontmatter)

    normalized = render_frontmatter(name, desc_lines) + normalize_body(body)

    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(normalized, encoding="utf-8")


def write_shared_assets() -> None:
    shared_ref = DST_ROOT / "_shared" / "references"
    shared_ref.mkdir(parents=True, exist_ok=True)

    src_contract = SRC_ROOT / "source-ingest" / "references" / "data-contracts.md"
    if not src_contract.exists():
        raise FileNotFoundError(f"missing source data contracts: {src_contract}")
    shutil.copy2(src_contract, shared_ref / "data-contracts.md")

    (shared_ref / "execution-envelope.md").write_text(
        """# Execution Envelope

All adapter-backed capability calls must return this shape:

```json
{
  "ok": true,
  "data": {},
  "error_code": null,
  "fallback_level": "native|adapter|degraded",
  "trace_id": "trace_..."
}
```

Field semantics:
- `ok`: true when operation succeeded at current or fallback level
- `data`: capability-specific payload
- `error_code`: stable machine-readable code when `ok = false`
- `fallback_level`: execution path used
- `trace_id`: audit correlation id for logs and replay

Soft-failure policy:
- `search` may return `ok=false` with `error_code=evidence_gap`; orchestration continues.
- `fetch` may return `ok=false` with `error_code=fetch_skipped`; source is skipped and audited.
- `spawn_role` may return `ok=false` with `error_code=role_spawn_unavailable`; orchestrator switches to serial role emulation.
""",
        encoding="utf-8",
    )

    (shared_ref / "capability-adapter.md").write_text(
        """# Generic Capability Adapter Contract

This repository uses provider-agnostic capability names:

- `search(query, recency?, locale?)`
- `fetch(url, timeout_sec?)`
- `spawn_role(role, prompt, io_paths)`
- `validate_json(path, schema_type)`
- `append_audit(audit_file, json_line)`

## Fallback Chains

### search
1. Native platform search
2. Adapter-backed search implementation
3. Degraded mode: emit `evidence_gap`, continue workflow with uncertainty note

### fetch
1. Native fetch/content extraction
2. Adapter-backed HTTP/script extraction
3. Degraded mode: emit `fetch_skipped`, skip source, continue

### spawn_role
1. Native sub-agent role dispatch
2. Adapter-backed role dispatch
3. Degraded mode: single-agent serial role emulation (`pro -> con -> judge`)

## Model Tier Mapping

Provider-specific model names are not used in generic skills. Use tier mapping:

- `fast`: low-latency draft and extraction tasks
- `balanced`: default debate and synthesis tasks
- `deep`: high-stakes verification and audit tasks

If a platform cannot pin tiers explicitly, default to `balanced`.
""",
        encoding="utf-8",
    )


def main() -> None:
    for skill in SKILLS:
        migrate_skill(skill)
    write_shared_assets()
    print(f"Migrated {len(SKILLS)} skills into {DST_ROOT}")


if __name__ == "__main__":
    main()
