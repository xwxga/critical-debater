#!/bin/bash
# init-workspace.sh — Create debate workspace directory structure
# 创建辩论工作区目录结构
#
# Usage: ./scripts/init-workspace.sh <workspace_dir> <topic> <rounds>
# Example: ./scripts/init-workspace.sh ./debate-workspace "Bitcoin vs Gold" 3

set -euo pipefail

WORKSPACE_DIR="${1:?Usage: $0 <workspace_dir> <topic> <rounds>}"
TOPIC="${2:?Usage: $0 <workspace_dir> <topic> <rounds>}"
ROUNDS="${3:-3}"
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Create directory structure / 创建目录结构
mkdir -p "$WORKSPACE_DIR"/{evidence,claims,rounds,reports,logs}

# Create round directories / 创建回合目录
for i in $(seq 1 "$ROUNDS"); do
  mkdir -p "$WORKSPACE_DIR/rounds/round_$i"
done

# Initialize config.json / 初始化配置
cat > "$WORKSPACE_DIR/config.json" <<EOF
{
  "topic": $(printf '%s' "$TOPIC" | python3 -c 'import sys,json; print(json.dumps(sys.stdin.read()))'),
  "round_count": $ROUNDS,
  "current_round": 0,
  "status": "initialized",
  "created_at": "$TIMESTAMP",
  "updated_at": "$TIMESTAMP"
}
EOF

# Initialize empty evidence store / 初始化空证据存储
echo '[]' > "$WORKSPACE_DIR/evidence/evidence_store.json"

# Initialize empty claim ledger / 初始化空声明账本
echo '[]' > "$WORKSPACE_DIR/claims/claim_ledger.json"

# Initialize empty audit trail / 初始化空审计日志
touch "$WORKSPACE_DIR/logs/audit_trail.jsonl"

# Log initialization / 记录初始化事件
AUDIT_LINE=$(cat <<EOF
{"timestamp":"$TIMESTAMP","action":"workspace_initialized","topic":$(printf '%s' "$TOPIC" | python3 -c 'import sys,json; print(json.dumps(sys.stdin.read()))'),"rounds":$ROUNDS}
EOF
)
echo "$AUDIT_LINE" >> "$WORKSPACE_DIR/logs/audit_trail.jsonl"

echo "Workspace initialized at $WORKSPACE_DIR"
echo "Topic: $TOPIC"
echo "Rounds: $ROUNDS"
