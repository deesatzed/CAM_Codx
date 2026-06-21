# New Computer Setup Walkthrough

This guide recreates the public CAM working layout on a different computer.
It keeps public GitHub repos separate from private local runtime state.

Use this when you want a new user or a clean machine to match the current CAM
hub-and-spoke structure.

## What Exists

| Repo or folder | Purpose | GitHub? |
|---|---|---|
| `CAM_Codx` | Codex-native workflow hub: docs, goals, adapters, setup guides, proof reports. | yes |
| `CAM_CAM` | Runtime engine: Repo Necromancer, Repo Rescue Desk, mining/runtime code, tests. | yes |
| `moriahcareframe` | Generated standalone product proof repo. | yes |
| `CAM_ALL` | Local operating overlay: clean clones, local state, scripts, clone proofs. | no |
| `CAM_ARCHIVE` | Local archive/provenance area for cleanup manifests. | no |

Expected public remotes:

```text
https://github.com/deesatzed/CAM_Codx.git
https://github.com/deesatzed/CAM_CAM.git
https://github.com/deesatzed/moriahcareframe.git
```

Current verified public roles:

- `CAM_Codx` explains and orchestrates.
- `CAM_CAM` executes runtime tooling.
- `moriahcareframe` proves generated products stay standalone.
- Local-only files such as `.env`, private adapter config, and `claw.db` stay
  out of GitHub.

## Validation Protocol

Move one step at a time. After each step:

- reply `C` to continue,
- reply `T` to stop and troubleshoot.

Do not continue after a failed command. Fix the failure first.

## Recommended Path: Setup Wizard

Use the wizard instead of manually copying files:

```bash
cd /path/to/CAM_Codx
python tools/cam_setup_wizard.py
```

For a non-interactive run with an existing CAM_CAM build:

```bash
python tools/cam_setup_wizard.py \
  --cam-home /Volumes/CAMADA/CAM_ALL \
  --cam-archive /Volumes/CAMADA/CAM_ARCHIVE \
  --existing-cam-cam /path/to/existing/CAM_CAM \
  --non-interactive
```

The wizard:

- creates the `CAM_ALL` and `CAM_ARCHIVE` layout,
- clones or updates `CAM_Codx`, `CAM_CAM`, and `moriahcareframe`,
- copies public config templates into `local_state`,
- optionally imports private runtime state from an existing CAM_CAM build,
- writes a setup report to `$CAM_HOME/reports/setup_report.md`,
- never writes `.env`, `claw.db`, or local override config into public Git
  clones.

## Prerequisites

Required:

- `git`
- `python3`
- shell with POSIX basics, such as `zsh` or `bash`

Recommended:

- Python 3.11 or 3.12
- `uv` for faster Python dependency installs
- Codex installed if you want to run `/goal`
- Node/npm only if you plan to run optional frontend UI surfaces
- API keys only if you plan to use model-backed CAM features

## Step 1: Choose The Local Workspace

Pick one local root. The examples use your home directory so they work on most
machines:

```bash
export CAM_HOME="$HOME/CAM_ALL"
export CAM_ARCHIVE="$HOME/CAM_ARCHIVE"

mkdir -p "$CAM_HOME"/{repos,local_state/CAM_CAM/{data,config,env},local_state/CAM_Codx/config,local_state/adapters,reports,clone_proofs,scripts}
mkdir -p "$CAM_ARCHIVE"
```

Check:

```bash
find "$CAM_HOME" -maxdepth 2 -type d | sort
find "$CAM_ARCHIVE" -maxdepth 1 -type d | sort
```

Expected:

- `repos/`
- `local_state/`
- `reports/`
- `clone_proofs/`
- `scripts/`

## Step 2: Clone Public Repos

Wizard equivalent:

```bash
python tools/cam_setup_wizard.py --cam-home "$CAM_HOME" --cam-archive "$CAM_ARCHIVE"
```

Manual reference:

```bash
cd "$CAM_HOME/repos"

git clone https://github.com/deesatzed/CAM_Codx.git
git clone https://github.com/deesatzed/CAM_CAM.git
git clone https://github.com/deesatzed/moriahcareframe.git
```

Check:

```bash
for repo in CAM_Codx CAM_CAM moriahcareframe; do
  echo "== $repo =="
  git -C "$CAM_HOME/repos/$repo" status --short --branch
  git -C "$CAM_HOME/repos/$repo" remote -v
done
```

Expected:

- each repo is on `main...origin/main`,
- each repo has a clean status,
- remotes point to `deesatzed`.

## Step 3: Verify The Hub Docs

```bash
cd "$CAM_HOME/repos/CAM_Codx"

git diff --check
python -m json.tool docs/repo_inventory/RETIREMENT_MANIFEST.json >/dev/null
python -m json.tool docs/repo_inventory/PUBLIC_REPO_CLEANUP_MANIFEST.json >/dev/null
```

Expected:

- all commands exit `0`,
- no output from `git diff --check`.

Read the orientation docs:

```bash
sed -n '1,160p' README.md
sed -n '1,180p' docs/QUICKSTART_CODEX.md
sed -n '1,180p' docs/WORKFLOW_REPO_NECROMANCER.md
```

## Step 4: Install CAM_CAM Runtime

```bash
cd "$CAM_HOME/repos/CAM_CAM"

python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip uv
python -m uv pip install -e ".[dev]"
```

Check:

```bash
PYTHONPATH=src python -m claw.cli --help
python -m pytest -q tests/test_repo_necromancer.py
git diff --check
```

Expected:

- CLI help prints,
- Repo Necromancer tests pass,
- `git diff --check` exits `0`.

## Step 5: Create Local Config Without Committing It

Wizard equivalent:

```bash
python tools/cam_setup_wizard.py \
  --cam-home "$CAM_HOME" \
  --cam-archive "$CAM_ARCHIVE" \
  --skip-clone
```

Manual reference:

Public-safe defaults are tracked in `CAM_CAM`, including:

- `claw.toml`
- `claw_cheap.toml`
- `claw_dspro.toml`
- `claw_grok.toml`
- `.env.example`

Private local overrides and real secrets must stay outside Git.

```bash
cd "$CAM_HOME/repos/CAM_CAM"

cp .env.example "$CAM_HOME/local_state/CAM_CAM/env/.env"
```

Then edit:

```text
$CAM_HOME/local_state/CAM_CAM/env/.env
```

Use your own keys only if you need model-backed features. Many deterministic
Repo Rescue Desk and Repo Necromancer checks do not require keys.

Copy CAM_Codx config templates into local-only files:

```bash
cd "$CAM_HOME/repos/CAM_Codx"

cp templates/config/cam-codx.env.example "$CAM_HOME/local_state/CAM_Codx/config/cam-codx.env"
cp templates/config/cam-cam-claw.example.toml "$CAM_HOME/local_state/CAM_CAM/config/claw.local.toml"
cp templates/config/adapter-config.example.toml "$CAM_HOME/local_state/adapters/adapter-config.local.toml"
```

Check:

```bash
find "$CAM_HOME/local_state" -maxdepth 4 -type f | sort
git -C "$CAM_HOME/repos/CAM_Codx" status --short
git -C "$CAM_HOME/repos/CAM_CAM" status --short
```

Expected:

- local config files exist under `local_state`,
- public repo status does not show `.env` or local-state files as tracked
  changes.

## Step 6: Import Or Initialize Runtime State

`claw.db` is local runtime state. It is intentionally not committed to GitHub.

Wizard equivalent:

```bash
python tools/cam_setup_wizard.py \
  --cam-home "$CAM_HOME" \
  --cam-archive "$CAM_ARCHIVE" \
  --existing-cam-cam "$EXISTING_CAM_CAM" \
  --non-interactive
```

Manual reference:

On a new machine, use one of these paths:

1. Let CAM initialize or seed a new local database during normal setup.
2. Point config at a private existing database you control.
3. Intentionally copy private runtime state from an existing CAM build into
   `CAM_ALL/local_state`.

### Option A: Start Fresh

Use this when the new machine should build its own local CAM state:

```text
$CAM_HOME/local_state/CAM_CAM/data/claw.db
```

Leave the DB path empty until CAM creates or seeds it. Do not commit the DB.

### Option B: Copy From An Existing Build

Use this when you already have a working CAM build and want the new computer to
use the same private runtime state.

Set the old build path. Example:

```bash
export EXISTING_CAM_CAM="/path/to/existing/CAM_CAM"
```

Copy the private DBs into local state, not into the public Git clone:

```bash
cp "$EXISTING_CAM_CAM/data/claw.db" "$CAM_HOME/local_state/CAM_CAM/data/claw.db"

if [ -f "$EXISTING_CAM_CAM/data/clawBU.db" ]; then
  cp "$EXISTING_CAM_CAM/data/clawBU.db" "$CAM_HOME/local_state/CAM_CAM/data/clawBU.db"
fi
```

Copy private environment config into local state:

```bash
if [ -f "$EXISTING_CAM_CAM/.env" ]; then
  cp "$EXISTING_CAM_CAM/.env" "$CAM_HOME/local_state/CAM_CAM/env/.env"
  chmod 600 "$CAM_HOME/local_state/CAM_CAM/env/.env"
fi
```

Copy existing TOML configs as local overrides:

```bash
for name in claw claw_cheap claw_dspro claw_grok; do
  if [ -f "$EXISTING_CAM_CAM/${name}.toml" ]; then
    cp "$EXISTING_CAM_CAM/${name}.toml" "$CAM_HOME/local_state/CAM_CAM/config/${name}.local.toml"
  fi
done
```

If the existing build has local Codex or adapter config, copy it to local state
only:

```bash
if [ -f "$HOME/.codex/config.toml" ]; then
  cp "$HOME/.codex/config.toml" "$CAM_HOME/local_state/CAM_Codx/config/codex.local.toml"
fi
```

Do not copy private runtime state into:

```text
$CAM_HOME/repos/CAM_Codx
$CAM_HOME/repos/CAM_CAM
$CAM_HOME/repos/moriahcareframe
```

Validate the imported state without printing secrets:

```bash
ls -lh "$CAM_HOME/local_state/CAM_CAM/data" || true
find "$CAM_HOME/local_state/CAM_CAM/config" -maxdepth 1 -type f | sort
test -f "$CAM_HOME/local_state/CAM_CAM/env/.env" && ls -l "$CAM_HOME/local_state/CAM_CAM/env/.env"

if [ -f "$CAM_HOME/local_state/CAM_CAM/data/claw.db" ]; then
  sqlite3 "$CAM_HOME/local_state/CAM_CAM/data/claw.db" '.tables'
fi

python - <<'PY'
import os
import tomllib
from pathlib import Path
root = Path(os.environ["CAM_HOME"]) / "local_state" / "CAM_CAM" / "config"
for path in root.glob("*.toml"):
    tomllib.loads(path.read_text())
    print(f"ok {path}")
PY
```

Confirm public repos stayed clean:

```bash
git -C "$CAM_HOME/repos/CAM_Codx" status --short
git -C "$CAM_HOME/repos/CAM_CAM" status --short
```

## Step 7: Run Repo Necromancer On Two Local Repos

Choose two source repos. They can be any two local repos you want to profile
read-only.

```bash
export SOURCE_A="/path/to/source-a"
export SOURCE_B="/path/to/source-b"
export PRODUCT_NAME="MyProduct"
export PRODUCT_REPO="$CAM_HOME/repos/$PRODUCT_NAME"
export PACKET_DIR="$CAM_HOME/repos/CAM_CAM/docs/showpieces/repo_necromancer/my_product"

cd "$CAM_HOME/repos/CAM_CAM"

python scripts/repo_necromancer.py \
  --repo-a "$SOURCE_A" \
  --repo-b "$SOURCE_B" \
  --out-dir "$PACKET_DIR" \
  --product-name "$PRODUCT_NAME" \
  --standalone-repo "$PRODUCT_REPO" \
  --merger-brief "Build the smallest useful merged repo first. Show what was borrowed, why, and which files are safe to touch next."
```

Expected:

- `PACKET_DIR` contains `CAM_CODEX_GOAL.md`, `evidence.json`, and report docs.
- `PRODUCT_REPO` is a standalone generated product repo if the generator path
  completed that stage.
- The merger brief appears in the packet and standalone README so Codex knows
  the intended outcome.
- source repos are not intentionally modified.

## Step 8: Continue The Packet In Codex

```bash
cd "$CAM_HOME/repos/CAM_Codx"
codex
```

Inside Codex:

```text
/goal /absolute/path/to/CAM_CODEX_GOAL.md
```

If `/goal` is unavailable, paste the generated `CAM_CODEX_GOAL.md` and say:

```text
Use this as the active completion contract. Build the standalone repo, preserve
source-repo read-only boundaries, and verify tests/smoke before claiming done.
```

## Step 9: Validate The Generated Product

Adjust the commands to the generated product's README. For a Python product
using the MoriahCareFrame pattern:

```bash
cd "$PRODUCT_REPO"

PYTHONPATH=src python -m pytest -q
sh scripts/smoke.sh
git diff --check
git status --short --branch
```

Expected:

- tests pass,
- smoke command passes,
- generated product status is clean or only shows files intentionally produced
  by the smoke command and documented by the product README.

## Step 10: Create A Fresh-Clone Proof

Use this to prove GitHub clone behavior, not just your working checkout:

```bash
export PROOF_DIR="$CAM_HOME/clone_proofs/$(date +%Y-%m-%d-%H%M%S)"
mkdir -p "$PROOF_DIR"

git clone https://github.com/deesatzed/CAM_Codx.git "$PROOF_DIR/CAM_Codx"
git clone https://github.com/deesatzed/CAM_CAM.git "$PROOF_DIR/CAM_CAM"
git clone https://github.com/deesatzed/moriahcareframe.git "$PROOF_DIR/moriahcareframe"

for repo in CAM_Codx CAM_CAM moriahcareframe; do
  echo "== $repo =="
  git -C "$PROOF_DIR/$repo" status --short --branch
  git -C "$PROOF_DIR/$repo" rev-parse HEAD
done
```

Run clone checks:

```bash
cd "$PROOF_DIR/CAM_Codx"
git diff --check
python -m json.tool docs/repo_inventory/RETIREMENT_MANIFEST.json >/dev/null
python -m json.tool docs/repo_inventory/PUBLIC_REPO_CLEANUP_MANIFEST.json >/dev/null

cd "$PROOF_DIR/CAM_CAM"
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip uv
python -m uv pip install -e ".[dev]"
python -m pytest -q tests/test_repo_necromancer.py
git diff --check

cd "$PROOF_DIR/moriahcareframe"
PYTHONPATH=src python -m pytest -q
sh scripts/smoke.sh
git diff --check
```

Expected:

- all checks pass from fresh clones,
- public GitHub state is enough for clone-and-run verification,
- local-only state remains outside the repos.

## Troubleshooting Rules

If a step fails:

1. Stop immediately.
2. Capture the exact command and output.
3. Check current directory with `pwd`.
4. Check repo status with `git status --short --branch`.
5. Do not delete local state or cleanup folders to fix a setup issue.
6. Do not commit `.env`, `claw.db`, private adapter config, or local machine
   paths.

Common fixes:

| Symptom | Likely cause | First check |
|---|---|---|
| `No module named claw` | venv not active or package not installed | `which python`, `python -m uv pip install -e ".[dev]"` |
| pytest missing | dev extras not installed | `python -m uv pip install -e ".[dev]"` |
| `/goal` unavailable | Codex surface does not support slash command | paste goal contents manually |
| `claw.db` missing | new machine has no local DB yet | initialize/seed local DB or point config at one |
| git status shows `.env` | private file created in repo root | move it to `CAM_ALL/local_state` |

## Completion Definition

The setup is valid when:

- three public repos are cloned under `CAM_HOME/repos`,
- public repo statuses are clean,
- CAM_CAM Repo Necromancer tests pass,
- CAM_Codx JSON/diff checks pass,
- local config lives under `CAM_HOME/local_state`,
- no private DB or `.env` is committed,
- optional fresh-clone proof passes.
