---
name: source-ingest
description: >
  This skill should be used when the debate system needs to "search for evidence",
  "gather sources for a debate topic", "ingest and normalize sources", "fetch web content
  for evidence", "build the initial evidence store", or "find supporting data for arguments".
  Searches, fetches, and normalizes sources into EvidenceItem format for the debate evidence store.
  搜索、抓取并将来源规范化为 EvidenceItem 格式。
version: 0.1.0
---

# SourceIngest
# 来源获取

Search, fetch, and normalize sources into `EvidenceItem` format for the debate evidence store.
搜索、抓取并将来源规范化为 `EvidenceItem` 格式，供辩论证据存储使用。

## When to Use / 何时使用

- During debate initialization to gather initial evidence / 辩论初始化时收集初始证据
- During scheduled refresh to find updated sources / 定时刷新时查找更新来源
- When a debater needs additional evidence mid-round / 辩手在回合中需要额外证据时

## Input / 输入

- `topic`: The debate topic (string)
- `evidence_store_path`: Path to existing evidence_store.json (for deduplication)
- `search_scope`: "broad" (initialization) or "focused" (mid-round supplementary)

## Output / 输出

- Updated `evidence_store.json` with new `EvidenceItem` objects appended
- See `references/data-contracts.md` for EvidenceItem schema

## Core Workflow / 核心工作流

### Step 1: Keyword Generation (LLM) / 关键词生成

Given the debate topic, generate 3-5 diverse search queries using semantic understanding:

- Include queries targeting **fact-track** evidence (current state, recent data, breaking news)
- Include queries targeting **reasoning-track** evidence (mechanisms, historical parallels, academic research)
- Vary query angles: direct topic, related metrics, counterarguments, expert opinions
- Do NOT hardcode search queries; derive them from the actual topic context

### Step 2: Multi-Source Search / 多来源搜索

For each generated query:

1. Use **WebSearch** to find relevant results
2. For each promising result, use **WebFetch** to extract content
3. If WebFetch fails on JavaScript-heavy pages, note the URL for potential Playwright MCP fallback
4. Categorize `source_type`:
   - `web`: Standard web articles, blog posts
   - `twitter`: Tweets/X posts (signal layer only)
   - `academic`: Research papers, journal articles
   - `government`: Government reports, central bank statements
   - `other`: Everything else

### Step 3: Normalization / 规范化

For each fetched source, produce an `EvidenceItem`:

1. Extract the most relevant snippet (the passage supporting or refuting the topic)
2. Compute `hash` using `scripts/hash-snippet.sh <snippet_text>`
3. Assign `evidence_id`: `evi_` + first 8 characters of hash
4. Assign `credibility_tier` using LLM judgment based on publisher reputation:
   - `tier1_authoritative`: Government, central banks, AP/Reuters
   - `tier2_reputable`: Major newspapers, research institutions
   - `tier3_general`: Blogs, industry reports, press releases
   - `tier4_social`: Twitter, Reddit, forums
5. Assign `evidence_track`:
   - `fact`: If the snippet describes current state, recent events, live data
   - `reasoning`: If the snippet explains mechanisms, cites history, or analyzes trends
6. Set `freshness_status` to `current` initially (FreshnessCheck will refine later)
7. Record `published_at` and `retrieved_at` timestamps

### Step 4: Deduplication / 去重

1. Read existing `evidence_store.json`
2. Compare hashes of new items against existing items
3. Skip items with matching hashes (already ingested)
4. Append only genuinely new items

### Step 5: Persistence / 持久化

1. Write the updated array to `evidence_store.json`
2. Log the ingestion event via `scripts/append-audit.sh`

## Error Handling / 错误处理

| Scenario | Action |
|---|---|
| WebFetch fails for a URL | Retry once; if still fails, skip with note in audit trail |
| No search results for a query | Broaden keywords, try alternative angles |
| All queries return no results | Write `{"insufficient_evidence": true}` flag in evidence store; log warning |
| Duplicate evidence | Skip silently (dedup by hash) |

## Quality Guidelines / 质量准则

- Prefer tier1/tier2 sources over tier3/tier4 when available
- Gather evidence from BOTH sides of the debate topic (not just supporting evidence)
- Include at least one search query designed to find counterarguments
- For Twitter/X sources, always note them as `tier4_social` — they serve as signals, never as standalone proof
