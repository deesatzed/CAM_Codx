# Grok Build Integration

Grok Build can consume the same CAM packets as Codex and Claude Code. The
adapter contract is evidence-first: packets, receipts, source boundaries, and
verification output decide whether a build is complete.

## What Grok Build Consumes

- `CAM_CODEX_GOAL.md`
- `NECROMANCER_SHOWPIECE.md`
- `evidence.json`
- source repo paths and git heads
- target standalone repo path
- proof-of-done commands

## Packet Versus Product

A packet is not a standalone repo. A standalone repo must have its own runtime
code, README, tests, provenance notes, and smoke command.

## Source Receipts

Grok Build briefs should preserve:

- source repo path,
- source branch and commit,
- source dirty-state evidence,
- packet path,
- target repo path,
- exact verification commands.

## Reporting

Build reports should include changed files, test results, source-boundary
status, and any remaining product gaps.
