# IMPLEMENT.md

## Retrieved Methodologies (step: grok-controller-migration)

| pattern_id | name | fitness | source | status |
|---|---|---|---|---|
| `34cb9a68-3cce-48fd-b1c4-986c23bded63` | Creation mode: new | 0.9583 (22 green / 0 red) | unresolved source repo/path | applied narrowly |
| `fcbfea05-dfbf-4f4e-a826-631c51448bad` | Creation mode: new | 0.8333 (4 green / 0 red) | unresolved source repo/path | rejected for app-creation scope |

### One-line provenance citations

- `34cb9a68-3cce-48fd-b1c4-986c23bded63` - Creation mode: new - fitness 0.9583 (22 green / 0 red) - source: unresolved source repo/path
- `fcbfea05-dfbf-4f4e-a826-631c51448bad` - Creation mode: new - fitness 0.8333 (4 green / 0 red) - source: unresolved source repo/path

### Application plan

- APPLY `34cb9a68-3cce-48fd-b1c4-986c23bded63`: use the narrow CLI/test/documentation pattern only: add a standalone smoke command, keep versioned CLI semantics, and verify with focused tests.
- REJECT `fcbfea05-dfbf-4f4e-a826-631c51448bad`: the retrieved pattern is for creating an unrelated standalone app; this migration must not scaffold unrelated application structure.
