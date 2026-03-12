# Capability: Freshness Check

Use when user asks whether evidence is current/stale/timeless.

## Workflow
1. Load evidence items and identify claim usage context.
2. Apply dual-track policy:
   - fact track: may become stale
   - reasoning track: remains timeless
3. Update freshness_status and audit the decision basis.
4. Validate updated evidence JSON.
