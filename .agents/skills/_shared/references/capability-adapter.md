# Generic Capability Adapter Contract

This repository uses provider-agnostic capability names:

- `search(query, recency?, locale?)`
- `fetch(url, timeout_sec?)`
- `spawn_role(role, prompt, io_paths)`
- `validate_json(path, schema_type)`
- `append_audit(audit_file, json_line)`

## Fallback Chains

### search
1. Native platform search
2. Adapter-backed search implementation
3. Degraded mode: emit `evidence_gap`, continue workflow with uncertainty note

### fetch
1. Native fetch/content extraction
2. Adapter-backed HTTP/script extraction
3. Degraded mode: emit `fetch_skipped`, skip source, continue

### spawn_role
1. Native sub-agent role dispatch
2. Adapter-backed role dispatch
3. Degraded mode: single-agent serial role emulation (`pro -> con -> judge`)

## Model Tier Mapping

Provider-specific model names are not used in generic skills. Use tier mapping:

- `fast`: low-latency draft and extraction tasks
- `balanced`: default debate and synthesis tasks
- `deep`: high-stakes verification and audit tasks

If a platform cannot pin tiers explicitly, default to `balanced`.
