#!/bin/bash
# setup-skill-symlinks.sh — Create symlinks from .claude/skills/ to .agents/skills/
# 创建从 .claude/skills/ 到 .agents/skills/ 的符号链接
#
# Usage: bash scripts/setup-skill-symlinks.sh
# Idempotent: safe to run multiple times / 幂等：可多次安全运行

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CANONICAL="$PROJECT_ROOT/.agents/skills"
CLAUDE_SKILLS="$PROJECT_ROOT/.claude/skills"

if [ ! -d "$CANONICAL" ]; then
  echo "ERROR: $CANONICAL does not exist. Run from project root."
  exit 1
fi

# Ensure .claude/skills directory exists
mkdir -p "$CLAUDE_SKILLS"

count=0
for skill_dir in "$CANONICAL"/*/; do
  [ ! -d "$skill_dir" ] && continue
  skill_name=$(basename "$skill_dir")

  # Skip _shared (not a skill, shared resources)
  [ "$skill_name" = "_shared" ] && continue

  target="$CLAUDE_SKILLS/$skill_name"

  # Already a correct symlink → skip
  if [ -L "$target" ]; then
    current=$(readlink "$target")
    expected="../../.agents/skills/$skill_name"
    if [ "$current" = "$expected" ]; then
      echo "OK: .claude/skills/$skill_name (already linked)"
      count=$((count + 1))
      continue
    fi
    rm "$target"
  elif [ -d "$target" ]; then
    echo "WARNING: .claude/skills/$skill_name is a real directory, backing up to ${skill_name}.bak"
    mv "$target" "${target}.bak"
  fi

  # Create relative symlink
  ln -s "../../.agents/skills/$skill_name" "$target"
  echo "LINKED: .claude/skills/$skill_name -> .agents/skills/$skill_name"
  count=$((count + 1))
done

echo ""
echo "Done. $count skill symlinks ready."
