# CAM_Codx Setup Wrapper Implementation Plan

> **For Codex:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a setup-generated `cam-codx` wrapper so Codex users can approve one narrow CAM command prefix for DB/config writes.

**Architecture:** Extend `tools/cam_setup_wizard.py` with pure helper functions that resolve runtime paths and generate an executable wrapper under `CAM_HOME/scripts`. Keep private files out of Git and document the wrapper in setup docs and reports.

**Tech Stack:** Python standard library, pytest, Markdown docs, shell wrapper script.

---

### Task 1: Add Wrapper Generation Tests

**Files:**
- Modify: `tests/test_cam_setup_wizard.py`

**Step 1: Write tests for wrapper creation**

Add tests that create a temporary CAM_HOME and fake CAM_CAM checkout with:

- `.venv/bin/cam`;
- `claw.db`;
- `claw.toml`;
- `.env`.

Assert `create_cam_codx_wrapper(...)` writes `CAM_HOME/scripts/cam-codx`, marks
it executable, and includes the resolved DB/config/env/runtime paths.

**Step 2: Write tests for config forwarding behavior**

Run the generated wrapper with a fake `cam` executable that records its
arguments. Assert:

- `cam-codx status` forwards `status -c <config>`;
- `cam-codx status -c other.toml` does not append a second config;
- `cam-codx status --config other.toml` does not append a second config.

**Step 3: Run tests and expect failure**

Run:

```bash
python -m pytest -q tests/test_cam_setup_wizard.py
```

Expected: failure because `create_cam_codx_wrapper` does not exist yet.

### Task 2: Implement Wrapper Helpers

**Files:**
- Modify: `tools/cam_setup_wizard.py`

**Step 1: Add dataclass**

Add `CamCodxWrapper` with:

- `path`;
- `cam_cam`;
- `cam_cli`;
- `db`;
- `config`;
- `env_file`;
- `approval_prefix`.

**Step 2: Add `create_cam_codx_wrapper`**

Implement a function that:

- resolves paths;
- creates `CAM_HOME/scripts`;
- writes `cam-codx`;
- marks it `0700`;
- returns `CamCodxWrapper`.

**Step 3: Add shell wrapper body**

The script must:

```bash
#!/usr/bin/env bash
set -euo pipefail
CAM_CAM="..."
CAM_CLI="..."
CLAW_DB="..."
CLAW_CONFIG="..."
CAM_ENV="..."

for required in "$CAM_CLI" "$CLAW_DB" "$CLAW_CONFIG" "$CAM_ENV"; do
  if [ ! -e "$required" ]; then
    echo "cam-codx missing required path: $required" >&2
    exit 2
  fi
done

cd "$CAM_CAM"
set -a
source "$CAM_ENV"
set +a
export CLAW_DB_PATH="$CLAW_DB"
export CAM_CODEX_MCP_DB_PATH="$CLAW_DB"

has_config=0
for arg in "$@"; do
  if [ "$arg" = "-c" ] || [ "$arg" = "--config" ]; then
    has_config=1
  fi
done

if [ "$has_config" = "1" ]; then
  exec "$CAM_CLI" "$@"
fi
exec "$CAM_CLI" "$@" -c "$CLAW_CONFIG"
```

**Step 4: Run tests**

Run:

```bash
python -m pytest -q tests/test_cam_setup_wizard.py
```

Expected: pass.

### Task 3: Wire Wrapper Into Wizard Report

**Files:**
- Modify: `tools/cam_setup_wizard.py`
- Modify: `tests/test_cam_setup_wizard.py`

**Step 1: Add report coverage**

Update `write_report(...)` to optionally include the wrapper path and approval
prefix.

**Step 2: Add tests**

Assert report text includes:

- `cam-codx`;
- `Codex approval prefix`;
- wrapper path.

**Step 3: Run tests**

Run:

```bash
python -m pytest -q tests/test_cam_setup_wizard.py
```

Expected: pass.

### Task 4: Update Setup Docs

**Files:**
- Modify: `SETUP_ON_LAPTOP.md`
- Modify: `README.md`
- Modify: `PROGRESS.md`
- Modify: `DECISIONS.md`

**Step 1: Document the wrapper**

Add a beginner-friendly section explaining:

- why Codex needs a narrow approval command;
- where the wrapper lives;
- how to run `cam-codx status` and `cam-codx stats`;
- what approval prefix to grant.

**Step 2: Record the decision**

Add a `DECISIONS.md` entry stating that CAM_Codx uses a setup-generated wrapper
instead of broad filesystem permission.

**Step 3: Record progress**

Add a dated `PROGRESS.md` entry with implemented files and verification.

### Task 5: Add Reusable Skill Instructions

**Files:**
- Create: `templates/skills/cam-codx-setup/SKILL.md`

**Step 1: Create concise skill body**

The skill should instruct Codex to:

- locate CAM_Codx and CAM_CAM;
- run the setup wizard if needed;
- generate or verify `cam-codx`;
- run `cam-codx status` and `cam-codx stats`;
- ask for approval only for the wrapper prefix when unsandboxed writes are needed;
- never print secrets.

**Step 2: Keep it installable**

Do not include generated local paths. Use placeholders such as
`<CAM_HOME>/scripts/cam-codx`.

### Task 6: Verify

**Files:**
- No edits.

Run:

```bash
python -m pytest -q tests/test_cam_setup_wizard.py tests/test_agent_packs.py
python tools/generate_agent_packs.py --check
git diff --check
```

Expected: all pass.
