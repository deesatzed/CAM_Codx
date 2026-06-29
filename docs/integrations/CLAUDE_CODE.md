# Claude Code Integration

Claude Code can consume CAM artifacts as a bounded worker surface. CAM_Codx
remains the hub that defines the goal, proof gates, and provenance contract.

The current generated pack lives at
`agent-packs/claude-code/`. It is generated from the shared contract at
`agent-packs/contract/cam_agent_capabilities.json`.

## What Claude Code Consumes

- `CAM_CODEX_GOAL.md`
- `evidence.json`
- source repo paths and git heads
- target standalone repo path
- expected verification commands

## Operating Rules

- Read the generated goal before editing.
- Preserve source repo read-only boundaries unless the goal explicitly allows
  source edits.
- Write provenance before moving or adapting code.
- Run tests and smoke commands.
- Report exact changed files, commands, and outcomes.

## Handoff Shape

Use `templates/claude-code/repo-necromancer-handoff.md` for a bounded prompt.
It should tell Claude Code what it may edit, what it must not touch, and what
Markdown report format to return.

## MCP Setup

Use `agent-packs/claude-code/.mcp.json.example` as the starting point for a
project-scoped Claude Code MCP config. Keep real local paths and tokens out of
Git unless they are placeholders.

The default CAM runtime command is:

```bash
cam mcp --transport stdio
```

Verify from Claude Code with:

```bash
claude mcp list
```

Then check `/mcp` inside Claude Code.

After discovery passes and `.mcp.json` has real local CAM paths, run the pack
smoke script from the target project:

```bash
./smoke.sh
```

## Completion Evidence

Claude Code recommendations are not accepted until Codex classifies them as
Accepted, Rejected, or Needs Investigation and verification passes locally.
