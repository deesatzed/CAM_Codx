# Grok Build Brief

## Output Repo Path

`REPLACE_WITH_STANDALONE_REPO_PATH`

## Source Repo Paths

- `REPLACE_WITH_SOURCE_A`
- `REPLACE_WITH_SOURCE_B`

## Packet Path

`REPLACE_WITH_PACKET_PATH`

## Constraints

- Preserve source repos as read-only evidence.
- Do not publish secrets, local DBs, or private config.
- Do not count the packet as the standalone repo.
- Keep provenance and receipt files.

## Proof Of Done

- Runtime code exists in the output repo.
- README explains the product and source provenance.
- Tests pass.
- Smoke command passes.
- Git status is reported.
