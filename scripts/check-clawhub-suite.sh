#!/bin/bash
# check-clawhub-suite.sh
# Validate ClawHub/OpenClaw suite bundle structure and metadata.

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
BUNDLE_DIR="$ROOT_DIR/skills/critical-debater-suite"
SKILL_MD="$BUNDLE_DIR/SKILL.md"

if [ ! -f "$SKILL_MD" ]; then
  echo "ERROR: missing $SKILL_MD. Run scripts/build-suite-skill.py first." >&2
  exit 1
fi

# Ensure only one publishable skill folder exists under /skills.
SKILL_DIR_COUNT=$(find "$ROOT_DIR/skills" -mindepth 1 -maxdepth 1 -type d | wc -l | tr -d ' ')
if [ "$SKILL_DIR_COUNT" != "1" ]; then
  echo "ERROR: expected exactly 1 skill directory under skills/, got $SKILL_DIR_COUNT" >&2
  find "$ROOT_DIR/skills" -mindepth 1 -maxdepth 1 -type d >&2 || true
  exit 1
fi

ROOT_DIR="$ROOT_DIR" python3 - <<'PY'
from __future__ import annotations

import json
import os
import re
from pathlib import Path

root = Path(os.environ["ROOT_DIR"])
bundle = root / "skills" / "critical-debater-suite"
skill = bundle / "SKILL.md"
text = skill.read_text(encoding="utf-8")

if not text.startswith("---\n"):
    raise SystemExit("ERROR: SKILL.md missing frontmatter opening delimiter")
end = text.find("\n---\n", 4)
if end == -1:
    raise SystemExit("ERROR: SKILL.md missing frontmatter closing delimiter")
frontmatter = text[4:end]
body = text[end + 5 :]

required_keys = ["name:", "description:", "version:", "license:", "metadata:"]
for k in required_keys:
    if k not in frontmatter:
        raise SystemExit(f"ERROR: missing frontmatter key: {k[:-1]}")

meta_match = re.search(r"^metadata:\s*(\{.*\})\s*$", frontmatter, re.MULTILINE)
if not meta_match:
    raise SystemExit("ERROR: metadata must be one-line JSON object")

try:
    metadata = json.loads(meta_match.group(1))
except Exception as exc:
    raise SystemExit(f"ERROR: metadata JSON invalid: {exc}")

bins = metadata.get("openclaw", {}).get("requires", {}).get("bins", [])
if not isinstance(bins, list) or not bins:
    raise SystemExit("ERROR: metadata.openclaw.requires.bins must be a non-empty array")

# Check referenced supporting files inside SKILL.md body.
refs = set(re.findall(r"`((?:capabilities|references|scripts|examples)/[^`]+)`", body))
missing = sorted(str(bundle / ref) for ref in refs if not (bundle / ref).exists())
if missing:
    raise SystemExit("ERROR: missing referenced supporting files:\n- " + "\n- ".join(missing))

# Check bins cover script command usage.
script_text = "\n".join(
    p.read_text(encoding="utf-8", errors="replace")
    for p in (bundle / "scripts").glob("*")
    if p.is_file()
)
used = set()
for name in ("bash", "jq", "python3", "shasum"):
    if re.search(rf"\b{name}\b", script_text):
        used.add(name)

missing_bins = sorted(used - set(bins))
if missing_bins:
    raise SystemExit("ERROR: requires.bins missing commands used by scripts: " + ", ".join(missing_bins))

print("OK: frontmatter/metadata valid")
print(f"OK: referenced files present ({len(refs)})")
print("OK: requires.bins covers script usage")
PY

echo "OK: ClawHub suite checks passed"
