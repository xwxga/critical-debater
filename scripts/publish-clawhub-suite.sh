#!/bin/bash
# publish-clawhub-suite.sh
# Publish/sync critical-debater-suite skill to ClawHub.

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SKILL_DIR="$ROOT_DIR/skills/critical-debater-suite"
ACTION="${1:-publish}"
shift || true

if [ ! -d "$SKILL_DIR" ]; then
  echo "ERROR: missing $SKILL_DIR. Run scripts/build-suite-skill.py first." >&2
  exit 1
fi

if ! command -v clawhub >/dev/null 2>&1; then
  echo "ERROR: clawhub CLI not found in PATH" >&2
  exit 1
fi

case "$ACTION" in
  publish)
    echo "Publishing $SKILL_DIR"
    clawhub publish "$SKILL_DIR" "$@"
    ;;
  sync)
    echo "Syncing $SKILL_DIR"
    clawhub sync "$SKILL_DIR" "$@"
    ;;
  *)
    echo "Usage: $0 [publish|sync] [extra clawhub args...]" >&2
    exit 1
    ;;
esac
