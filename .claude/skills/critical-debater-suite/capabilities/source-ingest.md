# Capability: Source Ingest

Use when user asks to gather or refresh evidence.

## Workflow
1. Generate 3-5 diverse search queries from topic.
2. Collect source snippets and normalize into EvidenceItem.
3. Compute snippet hash via `scripts/hash-snippet.sh`.
4. Classify freshness (`current|stale|timeless`) and credibility tier.
5. Append unique items to `evidence_store.json` and validate.
6. Log ingestion via `scripts/append-audit.sh`.
