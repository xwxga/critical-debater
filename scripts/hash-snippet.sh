#!/bin/bash
# hash-snippet.sh — Compute SHA-256 hash of text input
# 计算文本的 SHA-256 哈希值
#
# Usage: ./scripts/hash-snippet.sh <text>
# Output: 64-character hex hash string

set -euo pipefail

TEXT="${1:?Usage: $0 <text>}"

echo -n "$TEXT" | shasum -a 256 | cut -d' ' -f1
