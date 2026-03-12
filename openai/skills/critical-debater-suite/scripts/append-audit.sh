#!/bin/bash
# append-audit.sh — Atomically append a JSONL line to audit trail
# 原子追加 JSONL 行到审计日志
#
# Usage: ./scripts/append-audit.sh <audit_file> <json_line>
# Uses temp file + mv pattern to prevent corruption on concurrent writes

set -euo pipefail

AUDIT_FILE="${1:?Usage: $0 <audit_file> <json_line>}"
JSON_LINE="${2:?Usage: $0 <audit_file> <json_line>}"

# Validate JSON line / 验证 JSON 行
if ! echo "$JSON_LINE" | jq empty 2>/dev/null; then
  echo "ERROR: Invalid JSON: $JSON_LINE" >&2
  exit 1
fi

# Ensure audit file exists / 确保审计文件存在
touch "$AUDIT_FILE"

# Atomic append: copy + append to temp, then mv / 原子追加
TEMP_FILE=$(mktemp "${AUDIT_FILE}.XXXXXX")
cp "$AUDIT_FILE" "$TEMP_FILE"
echo "$JSON_LINE" >> "$TEMP_FILE"
mv "$TEMP_FILE" "$AUDIT_FILE"
