# CAM_Codx Setup Wrapper Design

Date: 2026-07-06

## Problem

CAM users need Codex to run CAM commands that update `claw.db`, create SQLite
sidecars, and read local `.env`/TOML configuration. Codex sandboxes often allow
workspace writes only, so a CAM runtime installed outside the active workspace
can be readable but not writable. Asking users to approve broad shell access is
too vague and too risky.

## Decision

CAM_Codx setup should create a narrow, stable wrapper command named
`cam-codx`. The wrapper pins the CAM runtime directory, `.env`, `claw.db`, and
`claw.toml`, then delegates to the installed CAM CLI.

This gives Codex one bounded command prefix to request approval for:

```text
<cam-home>/scripts/cam-codx
```

The user can approve that wrapper instead of approving arbitrary shell commands
or changing global filesystem permissions.

## Architecture

`tools/cam_setup_wizard.py` remains the setup entrypoint. It already creates a
CAM overlay under `CAM_HOME`, imports private runtime state into
`local_state/`, and writes a setup report. The new behavior adds a generated
script under `CAM_HOME/scripts/cam-codx` and can install the
`cam-codx-setup` skill into the user's Codex skills directory.

The wrapper:

- changes directory to the resolved `CAM_CAM` checkout;
- sources the selected `.env` without printing secrets;
- exports `CLAW_DB_PATH` and `CAM_CODEX_MCP_DB_PATH`;
- delegates to `<CAM_CAM>/.venv/bin/cam`;
- appends `-c <selected claw.toml>` when the caller did not pass a config;
- preserves caller arguments for commands such as `status`, `stats`,
  `evaluate`, `mine`, and `enhance`.

## Data Flow

Inputs:

- CAM overlay root (`CAM_HOME`);
- CAM_CAM checkout path;
- selected DB path;
- selected TOML config path;
- selected `.env` path.

Output:

- executable wrapper at `CAM_HOME/scripts/cam-codx`;
- installed Codex skill at `<CODEX_HOME or ~/.codex>/skills/cam-codx-setup`;
- setup report section explaining the wrapper and the Codex approval prefix.

## Safety

The setup wizard must not print secret values. It may report that `.env` exists
and that an expected key name is present. It must not approve live CAM mutation
itself; it only creates a command with narrow scope so Codex can ask users for a
clear approval.

The wrapper must fail fast when required files are missing:

- CAM CLI;
- `claw.db`;
- `claw.toml`;
- `.env`.

## Testing

Tests should verify:

- wrapper content pins the expected paths;
- wrapper is executable;
- wrapper appends `-c <config>` when no config is supplied;
- wrapper does not append another config when `-c` or `--config` is supplied;
- setup reports include the approval prefix.

## Follow-On Skill

A reusable Codex skill named `cam-codx-setup` calls the wizard, verifies the
wrapper, runs `cam-codx status` and `cam-codx stats`, and asks the user to
approve the narrow wrapper prefix when Codex needs unsandboxed writes.
