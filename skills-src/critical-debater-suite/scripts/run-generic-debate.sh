#!/bin/bash
# run-generic-debate.sh
# Thin wrapper to invoke the real generic orchestrator implementation.

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

exec python3 scripts/debate_orchestrator_generic.py "$@"
