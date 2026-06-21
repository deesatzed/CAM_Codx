# CAM_Codx Hub Reorganization Implementation Plan

> **For Codex:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make `CAM_Codx` the professional main workflow hub for CAM-powered agentic development while keeping `CAM_CAM` as the runtime/base engine and adding equivalent integration surfaces for Claude Code and Grok Build.

**Architecture:** Use a hub-and-spoke model. `CAM_Codx` becomes the public-facing orchestration and documentation repo: goals, adapters, templates, examples, workflow docs, and product positioning. `CAM_CAM` remains the implementation engine for mining, repo analysis, generators, dashboards, and runtime code. `moriahcareframe` and future generated products remain separate output repos.

**Tech Stack:** Markdown docs, Codex `/goal` files, MCP/agent workflow templates, GitHub repo metadata, shell verification commands, optional static docs pages, and existing CAM/Codex/Claude/Grok local repos.

---

## Strategic Decision

Do not blindly merge `CAM_CAM`, `CAM_Codx`, generated product repos, Claude Code experiments, and Grok Build folders into one large repo.

Instead:

- `CAM_Codx` is the jewel: the clean front door for users who already work inside Codex and want CAM capabilities in that workflow.
- `CAM_CAM` is the base/runtime engine: mining, Repo Necromancer, dashboards, corpus, generators, and verification utilities.
- `CAM_Claude_Code` or equivalent docs/adapters should mirror the same pattern for Claude Code users.
- `CAM_Grok_Build` or equivalent docs/adapters should mirror the same pattern for Grok Build users.
- Generated products, such as `moriahcareframe`, stay separate repositories with provenance back to CAM.

This preserves clean ownership while making the public story easier:

> CAM_CAM powers it. CAM_Codx brings it into Codex. Claude/Grok adapters bring the same CAM engine into their workflows.

## Current Truth

Verified local state on 2026-06-21:

- Real `CAM_Codx` GitHub checkout:
  `/Volumes/WS4TB/repo622sn/CAM_Codx`
  remote: `https://github.com/deesatzed/CAM_Codx.git`
- Active `CAM_CAM` runtime checkout:
  `/Volumes/WS4TB/WS4TBr/CAM_Codx/CAM_CAM`
  remote: `https://github.com/deesatzed/CAM_CAM.git`
- `CAM_CAM` latest pushed Repo Necromancer commit:
  `40ba9f1 feat: add standalone Repo Necromancer generator`
- Generated standalone product repo:
  `/Volumes/WS4TB/WS4TBr/MoriahCareFrame`
  remote: `https://github.com/deesatzed/moriahcareframe.git`
  commit: `a82e42c Initial MoriahCareFrame runtime`
- Several local folders named `CAM_Codx` are not git repos. They are workspace/container folders and should not be treated as canonical checkouts.

## Target Repository Roles

### `deesatzed/CAM_Codx`

Purpose: primary user-facing hub for Codex users.

Owns:

- `GOAL.md` orchestration contract.
- Codex setup and quickstart.
- CAM workflow templates.
- Repo Necromancer execution guides.
- links to `CAM_CAM` runtime tools.
- examples showing generated product repos.
- compatibility docs for Claude Code and Grok Build.
- professional README, diagrams, and launch surface.

Does not own:

- heavy mining runtime,
- `claw.db`,
- CAM_CAM package internals,
- generated product app runtime code,
- duplicate copies of CAM_CAM source.

### `deesatzed/CAM_CAM`

Purpose: CAM runtime/base engine.

Owns:

- repo mining,
- workspace analysis,
- Repo Necromancer generator,
- dashboard/report generators,
- CAM database and corpus handling,
- runtime tests.

Must add:

- visible backlinks to `CAM_Codx` as the user-facing Codex workflow.
- a clear "use from Codex" section.
- stable artifact contracts for generated packets and standalone repos.

### `deesatzed/moriahcareframe`

Purpose: proof that CAM/Codex can generate a separate useful product repo.

Owns:

- its own runtime code,
- README,
- tests,
- provenance docs,
- smoke command,
- app-specific future development.

Must not become:

- the CAM platform repo,
- a storage place for CAM_CAM or CAM_Codx internals.

### Claude Code And Grok Build Surfaces

Purpose: make CAM useful outside Codex without diluting `CAM_Codx`.

Target structure:

- `docs/integrations/claude-code.md`
- `docs/integrations/grok-build.md`
- `templates/claude-code/`
- `templates/grok-build/`
- optional future repos only if the adapter surface grows large enough.

These should explain how Claude Code and Grok Build consume CAM artifacts, run Repo Necromancer outputs, record decisions, and preserve source-repo provenance.

## Task 1: Canonical Repo Inventory

**Files:**

- Create: `docs/repo_inventory/CANONICAL_REPOS.md`
- Create: `docs/repo_inventory/LOCAL_FOLDER_AUDIT.md`
- Create: `docs/repo_inventory/RETIREMENT_MANIFEST.json`
- Modify: `PROGRESS.md`

**Step 1: Write inventory command notes**

Document these commands in `LOCAL_FOLDER_AUDIT.md`:

```bash
find /Volumes/WS4TB -maxdepth 4 -type d -name .git 2>/dev/null | sed 's#/.git$##' | sort
git ls-remote --heads https://github.com/deesatzed/CAM_Codx.git
git ls-remote --heads https://github.com/deesatzed/CAM_CAM.git
git ls-remote --heads https://github.com/deesatzed/moriahcareframe.git
```

**Step 2: Run the inventory**

Run from any shell:

```bash
cd /Volumes/WS4TB/repo622sn/CAM_Codx
bash -lc 'find /Volumes/WS4TB -maxdepth 4 -type d -name .git 2>/dev/null | sed "s#/.git$##" | sort'
```

Expected: list includes the real `CAM_Codx`, `CAM_CAM`, and `MoriahCareFrame` repos plus many unrelated repos.

**Step 3: Classify folders**

In `CANONICAL_REPOS.md`, classify:

- canonical repo,
- runtime repo,
- generated product repo,
- workspace container,
- old backup/duplicate,
- unrelated project.

**Step 4: Create cleanup manifest**

In `RETIREMENT_MANIFEST.json`, list candidate local folders with:

```json
{
  "path": "/absolute/path",
  "classification": "keep|archive_candidate|delete_candidate|needs_user_review|do_not_touch",
  "reason": "short reason",
  "remote": "remote URL if any",
  "latest_commit": "short SHA if any",
  "risk": "low|medium|high"
}
```

Do not delete or move anything in this task.

**Step 5: Commit**

```bash
git add docs/repo_inventory PROGRESS.md
git commit -m "docs: inventory CAM repo topology"
```

## Task 1A: Configuration And Database Alignment

**Files:**

- Create: `docs/config/LOCAL_CONFIG_ALIGNMENT.md`
- Create: `docs/config/GITHUB_SAFE_CONFIG_GUIDE.md`
- Create: `docs/config/CONFIG_DRIFT_CHECKS.md`
- Create: `templates/config/cam-codx.env.example`
- Create: `templates/config/cam-cam-claw.example.toml`
- Create: `templates/config/adapter-config.example.toml`
- Modify: `PROGRESS.md`

**Why this is mandatory:**

`claw.db`, `claw.toml`, model routing config, `.env.example`, and local adapter
config determine whether CAM actually works locally. Public GitHub repos need
generic, safe templates. The reorg must preserve the local working setup while
making the public setup understandable and non-secret.

**Step 1: Inventory runtime-critical local files**

Inspect but do not copy sensitive contents from:

```bash
cd /Volumes/WS4TB/WS4TBr/CAM_Codx/CAM_CAM
ls -lh data/claw.db claw.toml claw_cheap.toml claw_grok.toml .env.example
find /Volumes/WS4TB/WS4TBr/CAM_Codx -maxdepth 3 -type f \
  \( -name 'config.toml' -o -name '.env.example' -o -name 'claw*.toml' \) \
  | sort
```

Record results in `docs/config/LOCAL_CONFIG_ALIGNMENT.md`.

**Step 2: Record database role without publishing the DB**

In `LOCAL_CONFIG_ALIGNMENT.md`, document:

- canonical local DB path,
- expected role of `claw.db`,
- which tools depend on it,
- how `CAM_Codx` points to it,
- how new users create or point to their own database,
- why `claw.db` must not be copied into `CAM_Codx` or GitHub.

Use metadata only. Allowed commands:

```bash
sqlite3 /Volumes/WS4TB/WS4TBr/CAM_Codx/CAM_CAM/data/claw.db '.tables'
sqlite3 /Volumes/WS4TB/WS4TBr/CAM_Codx/CAM_CAM/data/claw.db \
  "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name LIMIT 30;"
```

Do not dump table contents into docs unless the table and data are verified
non-sensitive and necessary.

**Step 3: Map local config to public templates**

In `GITHUB_SAFE_CONFIG_GUIDE.md`, create a table:

| Local file | Public/template file | Commit? | Why |
|---|---|---|---|
| `CAM_CAM/claw.toml` | `templates/config/cam-cam-claw.example.toml` | template only | model routing and runtime defaults |
| `CAM_CAM/.env` | never | no | secrets |
| `CAM_CAM/.env.example` | link/copy sanitized example | yes | onboarding |
| `CAM_CAM/data/claw.db` | never | no | local runtime database |
| `.codex/config.toml` | `templates/config/adapter-config.example.toml` | template only | Codex adapter wiring |

**Step 4: Create GitHub-safe templates**

`templates/config/cam-codx.env.example` must use placeholders only:

```bash
CAM_CODEX_MCP_DB_PATH=/absolute/path/to/your/CAM_CAM/data/claw.db
CAM_CODEX_MCP_OUTCOME_DB_PATH=
CAM_CODEX_MCP_DECISIONS_INDEX=
OPENROUTER_API_KEY=replace-me
GOOGLE_API_KEY=replace-me
XAI_API_KEY=replace-me
```

`templates/config/cam-cam-claw.example.toml` must include only safe generic
defaults. Do not include private local paths, real keys, or unsupported model
claims. It should show:

```toml
[database]
db_path = "data/claw.db"

[llm]
base_url = "https://openrouter.ai/api/v1"
fallback_models = []

[agents.codex]
enabled = true
mode = "openrouter"
api_key_env = "OPENROUTER_API_KEY"
model = "replace-with-openrouter-model-id"
```

`templates/config/adapter-config.example.toml` must show how Codex, Claude
Code, or Grok Build can point to CAM artifacts without hardcoding this user's
local paths.

**Step 5: Add drift checks**

`CONFIG_DRIFT_CHECKS.md` must include commands that compare local config shape
against public templates without exposing secrets:

```bash
python - <<'PY'
import tomllib
from pathlib import Path
for path in [
    "/Volumes/WS4TB/WS4TBr/CAM_Codx/CAM_CAM/claw.toml",
    "templates/config/cam-cam-claw.example.toml",
]:
    data = tomllib.loads(Path(path).read_text())
    print(path, sorted(data.keys()))
PY

grep -R "sk-" templates docs || true
grep -R "xai-" templates docs || true
grep -R "AIza" templates docs || true
```

Expected: TOML parses; no real-looking keys in docs/templates.

**Step 6: Verify**

Run:

```bash
cd /Volumes/WS4TB/repo622sn/CAM_Codx
python - <<'PY'
import tomllib
from pathlib import Path
for path in Path("templates/config").glob("*.toml"):
    tomllib.loads(path.read_text())
    print(f"ok {path}")
PY
grep -R "sk-" templates docs || true
grep -R "xai-" templates docs || true
grep -R "AIza" templates docs || true
git diff --check
```

Real keys found in templates/docs are a failure unless they are deliberately
fake examples that cannot authenticate.

**Step 7: Commit**

```bash
git add docs/config templates/config PROGRESS.md
git commit -m "docs: add CAM config and database alignment guide"
```

## Task 2: Reposition `CAM_Codx` As The Main Jewel

**Files:**

- Modify: `README.md`
- Create: `docs/ARCHITECTURE.md`
- Create: `docs/QUICKSTART_CODEX.md`
- Create: `docs/WORKFLOW_REPO_NECROMANCER.md`
- Create: `docs/examples/MORIAH_CAREFRAME_CASE_STUDY.md`
- Modify: `PROGRESS.md`

**Step 1: Rewrite the opening README frame**

The first screen of `README.md` should say:

```markdown
# CAM_Codx

CAM_Codx is the Codex-native command center for CAM: it lets a developer use
CAM_CAM's repo intelligence, provenance, and generators from inside the Codex
workflow they already use.
```

Required README sections:

- What CAM_Codx is.
- How it relates to CAM_CAM.
- How it relates to generated repos.
- Quickstart.
- Repo Necromancer example.
- Claude Code and Grok Build compatibility.
- Current status and honest limitations.

**Step 2: Add architecture doc**

`docs/ARCHITECTURE.md` must include:

```text
CAM_CAM runtime engine -> CAM_Codx workflow hub -> generated product repos
                         -> Claude Code adapter
                         -> Grok Build adapter
```

It must explicitly state that `CAM_Codx` does not vendor or duplicate `CAM_CAM`.

**Step 3: Add quickstart**

`docs/QUICKSTART_CODEX.md` must include:

```bash
git clone https://github.com/deesatzed/CAM_Codx.git
git clone https://github.com/deesatzed/CAM_CAM.git
```

Then show how a Codex user consumes a CAM_CAM generated goal or packet.

**Step 4: Add Repo Necromancer workflow**

`docs/WORKFLOW_REPO_NECROMANCER.md` must include the exact tested command shape:

```bash
python scripts/repo_necromancer.py \
  --repo-a /path/to/source-a \
  --repo-b /path/to/source-b \
  --out-dir docs/showpieces/repo_necromancer/my_pair \
  --product-name MyProduct \
  --standalone-repo /path/to/MyProduct
```

It must explain:

- packet versus standalone repo,
- why `--standalone-repo` matters,
- what files prove success,
- how Codex should continue from the generated repo.

**Step 5: Add case study**

`docs/examples/MORIAH_CAREFRAME_CASE_STUDY.md` must cite:

- CAM_CAM commit `40ba9f1`,
- MoriahCareFrame commit `a82e42c`,
- source repos,
- verification commands,
- what was learned from the earlier packet-only mistake.

**Step 6: Verify**

```bash
grep -n "CAM_CAM" README.md docs/ARCHITECTURE.md docs/QUICKSTART_CODEX.md
grep -n "moriahcareframe" README.md docs/examples/MORIAH_CAREFRAME_CASE_STUDY.md
git diff --check
```

**Step 7: Commit**

```bash
git add README.md docs/ARCHITECTURE.md docs/QUICKSTART_CODEX.md docs/WORKFLOW_REPO_NECROMANCER.md docs/examples/MORIAH_CAREFRAME_CASE_STUDY.md PROGRESS.md
git commit -m "docs: reposition CAM_Codx as CAM workflow hub"
```

## Task 3: Add Codex Goal And Template Surface

**Files:**

- Modify: `GOAL.md`
- Create: `templates/goals/repo-necromancer-standalone.md`
- Create: `templates/goals/cam-repo-audit.md`
- Create: `templates/goals/cam-generated-product-hardening.md`
- Create: `docs/TEMPLATE_GUIDE.md`
- Modify: `PROGRESS.md`

**Step 1: Root GOAL**

`GOAL.md` should become the durable contract for this reorganization. It must use:

```text
OUTCOME:
PROOF OF DONE:
SCOPE:
SAFETY / PROVENANCE:
CONSTRAINTS:
ITERATION:
STOP:
COMPLETE:
```

**Step 2: Repo Necromancer template**

`templates/goals/repo-necromancer-standalone.md` must include the hard rule:

```text
The task is incomplete unless the standalone repo path exists and contains
runtime code, tests, README, provenance docs, and a smoke command. Do not count
the packet directory as completion.
```

**Step 3: Audit template**

`templates/goals/cam-repo-audit.md` must support a non-destructive audit of a folder full of repos.

**Step 4: Generated product hardening template**

`templates/goals/cam-generated-product-hardening.md` must support taking a generated repo such as `moriahcareframe` from MVP to a stronger product while preserving provenance.

**Step 5: Verify**

```bash
grep -R "Do not count" templates/goals
grep -R "runtime code, tests, README, provenance docs" templates/goals
git diff --check
```

**Step 6: Commit**

```bash
git add GOAL.md templates docs/TEMPLATE_GUIDE.md PROGRESS.md
git commit -m "docs: add CAM_Codx goal templates"
```

## Task 4: Add Claude Code Adapter Surface

**Files:**

- Create: `docs/integrations/CLAUDE_CODE.md`
- Create: `templates/claude-code/CLAUDE.md`
- Create: `templates/claude-code/repo-necromancer-handoff.md`
- Create: `templates/claude-code/provenance-checklist.md`
- Modify: `README.md`
- Modify: `PROGRESS.md`

**Step 1: Adapter doc**

`docs/integrations/CLAUDE_CODE.md` must explain how Claude Code should consume CAM artifacts:

- read `CAM_CODEX_GOAL.md`,
- preserve source repo read-only boundaries,
- write provenance before code movement,
- run tests,
- report exact changed files.

**Step 2: Claude template**

`templates/claude-code/CLAUDE.md` should include:

```markdown
# CLAUDE.md

Use CAM artifacts as evidence. Do not treat generated packet demos as final
standalone products unless the goal explicitly says so.
```

**Step 3: Handoff template**

`templates/claude-code/repo-necromancer-handoff.md` must define:

- source repos,
- target standalone repo,
- safety boundaries,
- expected verification commands,
- final report format.

**Step 4: Verify**

```bash
grep -R "source repo" docs/integrations/CLAUDE_CODE.md templates/claude-code
grep -R "read-only" docs/integrations/CLAUDE_CODE.md templates/claude-code
git diff --check
```

**Step 5: Commit**

```bash
git add docs/integrations/CLAUDE_CODE.md templates/claude-code README.md PROGRESS.md
git commit -m "docs: add Claude Code CAM adapter surface"
```

## Task 5: Add Grok Build Adapter Surface

**Files:**

- Create: `docs/integrations/GROK_BUILD.md`
- Create: `templates/grok-build/BUILD_BRIEF.md`
- Create: `templates/grok-build/repo-necromancer-build-packet.md`
- Create: `templates/grok-build/provenance-checklist.md`
- Modify: `README.md`
- Modify: `PROGRESS.md`

**Step 1: Adapter doc**

`docs/integrations/GROK_BUILD.md` must explain:

- what CAM artifacts Grok Build consumes,
- how generated repos are distinguished from packets,
- how to preserve exact source receipts,
- how to report build/test evidence.

**Step 2: Build brief template**

`templates/grok-build/BUILD_BRIEF.md` must include:

- output repo path,
- source repo paths,
- packet path,
- constraints,
- proof of done.

**Step 3: Verify**

```bash
grep -R "standalone repo" docs/integrations/GROK_BUILD.md templates/grok-build
grep -R "packet" docs/integrations/GROK_BUILD.md templates/grok-build
git diff --check
```

**Step 4: Commit**

```bash
git add docs/integrations/GROK_BUILD.md templates/grok-build README.md PROGRESS.md
git commit -m "docs: add Grok Build CAM adapter surface"
```

## Task 6: Backlink From `CAM_CAM`

**Files in `CAM_CAM`:**

- Modify: `README.md`
- Modify: `docs/showpieces/repo_necromancer/USER_GUIDE.md`
- Create: `docs/integrations/CAM_CODEX.md`

**Step 1: Add CAM_Codx link to CAM_CAM README**

Add a section:

```markdown
## Use CAM_CAM From Codex

CAM_CAM is the runtime engine. CAM_Codx is the Codex-native workflow hub.
Start in CAM_Codx when you want Codex to consume CAM outputs.
```

**Step 2: Add integration doc**

`docs/integrations/CAM_CODEX.md` should link to:

- `https://github.com/deesatzed/CAM_Codx`
- Repo Necromancer workflow docs in `CAM_Codx`
- the tested `--standalone-repo` pattern.

**Step 3: Verify**

```bash
cd /Volumes/WS4TB/WS4TBr/CAM_Codx/CAM_CAM
python -m pytest -q tests/test_repo_necromancer.py
git diff --check
```

**Step 4: Commit**

```bash
git add README.md docs/showpieces/repo_necromancer/USER_GUIDE.md docs/integrations/CAM_CODEX.md
git commit -m "docs: link CAM_CAM runtime to CAM_Codx hub"
```

## Task 7: Professional Polish And Launch Surface

**Files:**

- Modify: `README.md`
- Create: `docs/LAUNCH_CHECKLIST.md`
- Create: `docs/STATUS.md`
- Create: `docs/FAQ.md`
- Create: `docs/REPO_MAP.md`
- Modify: `PROGRESS.md`

**Step 1: README polish**

The README must answer in the first 90 seconds:

- What is this?
- Who is it for?
- Why is CAM_Codx different?
- How does it connect to CAM_CAM?
- What can I run today?
- Where are examples?

**Step 2: Status page**

`docs/STATUS.md` must separate:

- implemented,
- verified locally,
- pushed to GitHub,
- planned,
- intentionally out of scope.

**Step 3: FAQ**

`docs/FAQ.md` must answer:

- Why are there multiple CAM repos?
- Why not one monorepo?
- What repo should a Codex user start with?
- What repo should a runtime/tooling contributor start with?
- What is a generated product repo?
- How do Claude Code and Grok Build fit?

**Step 4: Verify**

```bash
grep -n "What is this" README.md docs/FAQ.md
grep -n "CAM_CAM" docs/STATUS.md docs/REPO_MAP.md
grep -n "Claude Code" docs/FAQ.md docs/STATUS.md
grep -n "Grok Build" docs/FAQ.md docs/STATUS.md
git diff --check
```

**Step 5: Commit**

```bash
git add README.md docs/LAUNCH_CHECKLIST.md docs/STATUS.md docs/FAQ.md docs/REPO_MAP.md PROGRESS.md
git commit -m "docs: polish CAM_Codx launch surface"
```

## Task 8: Cross-Repo Verification And Push

**Files:**

- Create: `docs/reports/CAM_REPO_REORG_VERIFICATION_2026-06-21.md`
- Modify: `PROGRESS.md`

**Step 1: Verify remotes**

```bash
git -C /Volumes/WS4TB/repo622sn/CAM_Codx status --short --branch
git -C /Volumes/WS4TB/repo622sn/CAM_Codx remote -v
git -C /Volumes/WS4TB/WS4TBr/CAM_Codx/CAM_CAM status --short --branch
git -C /Volumes/WS4TB/WS4TBr/CAM_Codx/CAM_CAM remote -v
git -C /Volumes/WS4TB/WS4TBr/MoriahCareFrame status --short --branch
git -C /Volumes/WS4TB/WS4TBr/MoriahCareFrame remote -v
```

**Step 2: Verify tests**

```bash
cd /Volumes/WS4TB/WS4TBr/CAM_Codx/CAM_CAM
python -m pytest -q tests/test_repo_necromancer.py

cd /Volumes/WS4TB/WS4TBr/MoriahCareFrame
PYTHONPATH=src python -m pytest -q
sh scripts/smoke.sh
```

**Step 3: Verify docs**

```bash
cd /Volumes/WS4TB/repo622sn/CAM_Codx
find docs templates -type f | sort
grep -R "CAM_Codx" README.md docs templates
grep -R "CAM_CAM" README.md docs templates
grep -R "Claude Code" README.md docs templates
grep -R "Grok Build" README.md docs templates
git diff --check
```

**Step 4: Write verification report**

Record:

- repos touched,
- commits created,
- commands run,
- command outcomes,
- remaining dirty files,
- remaining duplicate folders,
- cleanup recommendations,
- GitHub URLs.

**Step 5: Push**

```bash
git -C /Volumes/WS4TB/repo622sn/CAM_Codx push origin main
git -C /Volumes/WS4TB/WS4TBr/CAM_Codx/CAM_CAM push origin main
git -C /Volumes/WS4TB/WS4TBr/MoriahCareFrame push origin main
```

## Non-Goals

- Do not delete or move old folders during this goal.
- Do not merge all code into one monorepo unless a later decision explicitly chooses monorepo migration.
- Do not copy `claw.db` into `CAM_Codx`.
- Do not publish local `.env`, API keys, private model endpoints, private local
  paths, or local-only database dumps.
- Do not claim a GitHub config is aligned with local runtime config unless the
  drift checks in `docs/config/CONFIG_DRIFT_CHECKS.md` have been run.
- Do not put generated product app code into `CAM_Codx`.
- Do not present Claude Code or Grok Build adapters as fully implemented runtime plugins unless verification proves it.
- Do not weaken or remove existing tests.

## Final Acceptance

The reorganization is done only when:

- `CAM_Codx` clearly reads as the main workflow hub.
- `CAM_CAM` clearly reads as the runtime/base engine.
- Claude Code and Grok Build have parallel adapter docs/templates.
- generated product repos are described as separate outputs.
- `claw.db`, `claw.toml`, `.env.example`, model routing, and adapter configs are
  mapped into local-only versus GitHub-safe public templates.
- duplicate local folders are inventoried and classified.
- no destructive cleanup has occurred without explicit approval.
- all touched repos have clean or intentionally documented git status.
- every claim in README/docs is supported by a command, file path, or GitHub URL.
