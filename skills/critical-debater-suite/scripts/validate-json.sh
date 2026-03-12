#!/bin/bash
# validate-json.sh — Validate JSON files against data contract schemas
# 验证 JSON 文件是否符合数据契约
#
# Usage: ./scripts/validate-json.sh <file> <schema_type>
# schema_type: config | evidence_item | claim_item | judge_ruling | final_report | pro_turn | con_turn
#
# Exit 0 = valid, Exit 1 = invalid (prints errors to stderr)

set -euo pipefail

FILE="${1:?Usage: $0 <file> <schema_type>}"
SCHEMA="${2:?Usage: $0 <file> <schema_type>}"

if [ ! -f "$FILE" ]; then
  echo "ERROR: File not found: $FILE" >&2
  exit 1
fi

# Check valid JSON first / 先检查是否为合法 JSON
if ! jq empty "$FILE" 2>/dev/null; then
  echo "ERROR: Invalid JSON in $FILE" >&2
  exit 1
fi

# Schema-specific required field checks / 按 schema 检查必需字段
case "$SCHEMA" in
  config)
    REQUIRED='["topic", "round_count", "current_round", "status", "created_at"]'
    ;;
  evidence_item)
    REQUIRED='["evidence_id", "source_type", "url", "snippet", "hash", "credibility_tier", "freshness_status", "evidence_track"]'
    ;;
  claim_item)
    REQUIRED='["claim_id", "round", "speaker", "claim_type", "claim_text", "evidence_ids", "status"]'
    ;;
  judge_ruling)
    REQUIRED='["round", "verification_results", "mandatory_response_points", "round_summary"]'
    ;;
  final_report)
    REQUIRED='["topic", "total_rounds", "verified_facts", "probable_conclusions", "contested_points", "to_verify", "scenario_outlook", "watchlist_24h"]'
    ;;
  pro_turn|con_turn)
    REQUIRED='["round", "side", "arguments", "rebuttals"]'
    ;;
  *)
    echo "ERROR: Unknown schema type: $SCHEMA" >&2
    echo "Valid types: config, evidence_item, claim_item, judge_ruling, final_report, pro_turn, con_turn" >&2
    exit 1
    ;;
esac

# Check required fields / 检查必需字段
ERRORS=0
for field in $(echo "$REQUIRED" | jq -r '.[]'); do
  # Handle both single object and array of objects
  IS_ARRAY=$(jq 'type == "array"' "$FILE")
  if [ "$IS_ARRAY" = "true" ]; then
    # For arrays, check first element (if exists)
    HAS_ELEMENTS=$(jq 'length > 0' "$FILE")
    if [ "$HAS_ELEMENTS" = "true" ]; then
      HAS_FIELD=$(jq --arg f "$field" '.[0] | has($f)' "$FILE")
      if [ "$HAS_FIELD" = "false" ]; then
        echo "ERROR: Missing required field '$field' in first element of $FILE" >&2
        ERRORS=$((ERRORS + 1))
      fi
    fi
  else
    HAS_FIELD=$(jq --arg f "$field" 'has($f)' "$FILE")
    if [ "$HAS_FIELD" = "false" ]; then
      echo "ERROR: Missing required field '$field' in $FILE" >&2
      ERRORS=$((ERRORS + 1))
    fi
  fi
done

if [ $ERRORS -gt 0 ]; then
  echo "FAILED: $ERRORS missing field(s) in $FILE (schema: $SCHEMA)" >&2
  exit 1
fi

echo "OK: $FILE validates against $SCHEMA"
exit 0
