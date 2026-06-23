# Grok Build Integration

Grok Build can consume the same CAM packets as Codex and Claude Code. The
adapter contract is evidence-first: packets, receipts, source boundaries, and
verification output decide whether a build is complete.

The current generated pack lives at `agent-packs/grok-build/`. It is generated
from the shared contract at
`agent-packs/contract/cam_agent_capabilities.json`.

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

## Pack Setup

Use the generated files in `agent-packs/grok-build/`:

- `AGENTS.md` for project-level behavior rules.
- `.grok/config.toml.example` for local CAM MCP config.
- `.grok/skills/cam-agent/SKILL.md` for CAM usage instructions.
- `.grok/hooks/pre-tool-cam-guard.sh` as an optional mutating-tool guard.
- `headless-smoke.sh` as a starting smoke command when Grok credentials are
  available.

The default CAM runtime command is:

```bash
cam mcp --transport stdio
```

Verify discovery with:

```bash
grok inspect
```

Keep xAI Remote MCP endpoint credentials outside Git.
