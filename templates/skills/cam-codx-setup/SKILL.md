---
name: cam-codx-setup
description: Install, verify, or repair CAM_Codx plus CAM_CAM for Codex use. Use when a user wants CAM setup, CAM_Codx install, CAM_CAM install, claw.db configuration, Codex approval for CAM DB writes, or a reusable cam-codx wrapper command.
---

# CAM_Codx Setup

Use this skill to make CAM usable from Codex without broad filesystem approval.
CAM_Codx owns setup guidance and workflow assets. CAM_CAM owns the runtime,
`cam` CLI, local `.env`, `claw.db`, and TOML config.

## Workflow

1. Identify paths:
   - CAM_Codx checkout;
   - CAM_CAM checkout;
   - `claw.db`;
   - `claw.toml`;
   - `.env`.
2. Never print secret values. Check `.env` key presence by name only.
3. Verify CAM_CAM has `.venv/bin/cam`.
4. Run CAM_Codx setup wizard to create or verify the wrapper:

```bash
python tools/cam_setup_wizard.py \
  --cam-home <CAM_HOME> \
  --skip-clone \
  --wrapper-cam-cam <CAM_CAM> \
  --wrapper-db <CAM_CAM>/claw.db \
  --wrapper-config <CAM_CAM>/claw.toml \
  --wrapper-env <CAM_CAM>/.env \
  --non-interactive
```

5. Use the generated wrapper for CAM checks:

```bash
<CAM_HOME>/scripts/cam-codx status
<CAM_HOME>/scripts/cam-codx stats
```

6. If Codex sandboxing blocks CAM DB or SQLite sidecar writes, ask the user to
   approve only this bounded command prefix:

```text
<CAM_HOME>/scripts/cam-codx
```

## Safety

- Do not request approval for arbitrary `bash`, `python`, or shell heredocs.
- Do not copy `.env` into Git-tracked paths.
- Do not make `claw.db` public or commit it.
- Stop if `claw.db` or config paths are ambiguous.
- Ask before overwriting an existing DB, TOML, or `.env`.

## Verification

Report:

- wrapper path;
- DB/config/env paths used, without secret values;
- `cam-codx status` result;
- `cam-codx stats` methodology count;
- any missing credentials or blocked write paths.
