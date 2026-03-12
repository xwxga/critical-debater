# Execution Envelope

All adapter-backed capability calls must return this shape:

```json
{
  "ok": true,
  "data": {},
  "error_code": null,
  "fallback_level": "native|adapter|degraded",
  "trace_id": "trace_..."
}
```

Field semantics:
- `ok`: true when operation succeeded at current or fallback level
- `data`: capability-specific payload
- `error_code`: stable machine-readable code when `ok = false`
- `fallback_level`: execution path used
- `trace_id`: audit correlation id for logs and replay

Soft-failure policy:
- `search` may return `ok=false` with `error_code=evidence_gap`; orchestration continues.
- `fetch` may return `ok=false` with `error_code=fetch_skipped`; source is skipped and audited.
- `spawn_role` may return `ok=false` with `error_code=role_spawn_unavailable`; orchestrator switches to serial role emulation.
