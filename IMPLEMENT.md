# Pull, Mine, and Review CAM Skill Implementation

## Retrieved Methodologies (step: task-0-boundary)

| pattern_id | name | fitness | source | status |
|---|---|---|---|---|
| `1410402d-7cd6-4a97-8636-82fb62660dcf` | Idempotent cache + incremental rebuild with SHA256 manifest | 0.6667 (1 green / 0 red) | graphify/provenance unavailable | stale |
| `e4194e64-8230-4b16-8715-a7c164ac2a15` | Autonomous Research Loop via Git Branching | 0.75 (2 green / 0 red) | autoresearch-macos/provenance unavailable | stale |

### One-line provenance citations

- `1410402d-7cd6-4a97-8636-82fb62660dcf` - Idempotent cache + incremental rebuild with SHA256 manifest - fitness 0.6667 (1 green / 0 red) - source: graphify/provenance unavailable
- `e4194e64-8230-4b16-8715-a7c164ac2a15` - Autonomous Research Loop via Git Branching - fitness 0.75 (2 green / 0 red) - source: autoresearch-macos/provenance unavailable

### Application plan

- APPLY `1410402d-7cd6-4a97-8636-82fb62660dcf`: use CAM's existing `--changed-only` mining mode and record before/after evidence, without introducing a new cache or modifying CAM_CAM runtime behavior.
- APPLY `e4194e64-8230-4b16-8715-a7c164ac2a15`: isolate any meaningful-result candidate through the existing manager-backed, single-use, supervised `--skip-swap` workflow; a candidate verdict can never promote, swap, or alter live configuration.

Both recalled records are stale and lack a resolved source path. They inform only the explicit safety boundaries above; tests and current CAM_CAM CLI behavior remain the acceptance authority.
