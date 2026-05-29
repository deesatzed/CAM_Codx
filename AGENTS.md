# AGENTS.md

## Grok Controller Rules

Grok is the primary controller for this repository.

- Use `grok` for interactive controller sessions.
- Use `grok -p "<prompt>"` or `grok agent headless` for non-interactive controller runs, depending on the integration surface.
- Use `grok inspect --json` to verify discovered project rules and MCP configuration.
- Use `grok mcp doctor cam_cam --json` to diagnose the CAM librarian MCP server.

## CAM Librarian Contract

The CAM librarian remains a four-tool MCP server:

- `cam_recall`
- `cam_provenance`
- `cam_decisions_search`
- `cam_record_outcome`

No fifth CAM MCP tool is allowed in this repository without a new explicit decision.

## Provenance Workflow

Before applying a mined methodology, recall it and cite provenance in `IMPLEMENT.md`.
After a verified step that used a recalled methodology, record the outcome through `cam_record_outcome`.

## Compatibility Notes

The Python package name `claw_codex_mcp` and console command `cam-codex-mcp` are compatibility surfaces. They do not make Codex the controller.

The `.codex/` tree is legacy compatibility material unless a task explicitly targets it. Do not use `.codex/config.toml` as the active controller configuration for Grok runs.

## Core Rule

Grok controls. Tests arbitrate. Markdown remembers. CAM librarian cites.
