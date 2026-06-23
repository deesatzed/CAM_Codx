# Repo Map

## Main Public Flow

```text
CAM_CAM -> MCP/CLI/runtime -> CAM_Codx -> generated agent packs
CAM_CAM -> packet / CAM_CODEX_GOAL.md -> CAM_Codx -> standalone product repo
```

## Current Local Paths

| Path | Meaning |
|---|---|
| `/Volumes/WS4TB/repo622sn/CAM_Codx` | Canonical CAM_Codx hub checkout for this goal. |
| `/Volumes/WS4TB/WS4TBr/CAM_Codx/CAM_CAM` | Runtime CAM_CAM checkout named by the goal. |
| `/Volumes/WS4TB/WS4TBr/MoriahCareFrame` | Generated standalone product repo. |
| `/Volumes/WS4TB/CAM_ALL` | Local clean operating overlay. |
| `/Volumes/WS4TB/CAM_ARCHIVE` | Non-destructive archive staging area. |

## Generated Agent Packs

| Pack | Purpose |
|---|---|
| `agent-packs/claude-code` | Claude Code MCP config, CLAUDE.md, command, and skill templates. |
| `agent-packs/gemini` | Gemini CLI/API CAM instructions, settings example, and skill template. |
| `agent-packs/grok-build` | Grok Build AGENTS.md, .grok config, skill, hook, and headless smoke template. |

## GitHub URLs

- `https://github.com/deesatzed/CAM_Codx`
- `https://github.com/deesatzed/CAM_CAM`
- `https://github.com/deesatzed/moriahcareframe`
