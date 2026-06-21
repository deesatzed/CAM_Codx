# Claude Code Integration

Claude Code can consume CAM artifacts as a bounded worker surface. CAM_Codx
remains the hub that defines the goal, proof gates, and provenance contract.

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

## Completion Evidence

Claude Code recommendations are not accepted until Codex classifies them as
Accepted, Rejected, or Needs Investigation and verification passes locally.
