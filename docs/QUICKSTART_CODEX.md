# Codex Quickstart

> **Current state:** follow the specialized-skill commands in this guide.
> **Approved target:** setup will install one `cam-codx` skill, and the user
> will say `Use CAM_Codx to <desired outcome>` for all normal CAM work. The
> consolidation is approved and planned but not yet implemented.

## What You Are Installing

Start here if you already have Codex installed and want Codex to use CAM.

The pieces are:

```text
Codex     = the AI coding operator you talk to
CAM_Codx  = the Codex-facing workflow hub: skills, setup docs, goals, templates
CAM_CAM   = the CAM engine: the `cam` command, repo analysis, mining, memory
claw.db   = CAM's local knowledge database
cam-codx  = the safe wrapper command Codex uses to operate CAM_CAM
```

The normal flow is:

```text
clone CAM_CAM and CAM_Codx
install CAM_CAM
copy or create claw.db, claw.toml, and .env
run the CAM_Codx setup wizard
start Codex in your project
say: Use cam-codx-setup to verify CAM.
```

## What The Skill Adds

The `cam-codx-setup` skill lets Codex verify and use CAM without broad
filesystem approval. It teaches Codex to:

- find `CAM_Codx` and `CAM_CAM`;
- verify `claw.db`, `claw.toml`, and `.env` without printing secrets;
- use the setup-generated `cam-codx` wrapper;
- ask the user to approve only the narrow wrapper command;
- run CAM health checks such as `status` and `stats`;
- report the exact CAM paths and verification result.

After setup is verified, Codex can use CAM_Codx/CAM_CAM to:

- evaluate a repo before editing it;
- inspect project structure, tests, docs, and config;
- search or apply CAM methodology memory;
- generate build plans and `GOAL.md` contracts;
- run dry-run enhancement planning before live mutation;
- validate claims with command evidence;
- save durable reports such as `CAM_SESSION_REPORT.md`.

For routine software-engineering work, invoke the manager skill explicitly:

```text
Use cam-codx-swe to manage this build/update task with CAM recall and evidence gates.
```

This is not an implicit mining hook. Mining, provider spend, model promotion,
and CAM self-enhancement require their own bounded packet and phase approval.
Read [CAM_Codx Program Manager](CAM_CODEX_PROGRAM_MANAGER.md) for the exact
flow.

For the earlier question—what prior work, mistakes, or even cross-domain ideas
should shape a new build, or should an existing project continue, be mitigated,
or be re-developed—use the separate Development Brief skill:

```text
Use cam-codx-development-brief to help me start this new project from relevant prior work.
```

```text
Use cam-codx-development-brief to decide whether this in-progress repository should continue, be mitigated, or be re-developed.
```

It labels each recommendation as a direct precedent, transferable analogy, or
new hypothesis. Its default reads only the named target and explicitly supplied
primary CAM corpus; it does not mine, contact a provider, write retrieval
telemetry, run target tests, or edit code. Read
[CAM Development Brief](CAM_DEVELOPMENT_BRIEF.md) for the command form and
scope-expansion gate.

## Clone The Hub And Engine

```bash
mkdir -p ~/CAM
cd ~/CAM
git clone https://github.com/deesatzed/CAM_Codx.git
git clone https://github.com/deesatzed/CAM_CAM.git
```

Install the CAM engine:

```bash
cd ~/CAM/CAM_CAM
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Then add the private runtime files that do not live on GitHub:

```text
~/CAM/CAM_CAM/claw.db
~/CAM/CAM_CAM/claw.toml
~/CAM/CAM_CAM/.env
```

If `.env` does not exist yet:

```bash
cd ~/CAM/CAM_CAM
cp .env.example .env
```

Edit `.env` and add your API keys. Do not commit or share `.env`.

## Install The Codex Skill And Wrapper

Run this from the CAM_Codx checkout:

```bash
cd ~/CAM/CAM_Codx
python tools/cam_setup_wizard.py \
  --cam-home ~/CAM \
  --skip-clone \
  --install-codex-skill \
  --non-interactive
```

This creates:

```text
~/CAM/scripts/cam-codx
~/.codex/skills/cam-codx-setup/SKILL.md
~/.codex/skills/cam-codx-swe/SKILL.md
~/.codex/skills/cam-codx-development-brief/SKILL.md
~/.codex/skills/cam-codx-pull-mine-dir/SKILL.md
```

Test CAM through the wrapper:

```bash
~/CAM/scripts/cam-codx status
~/CAM/scripts/cam-codx stats
```

When Codex asks for permission, approve only this command prefix:

```text
~/CAM/scripts/cam-codx
```

That gives Codex a bounded way to let CAM update `claw.db` and SQLite sidecar
files without granting arbitrary shell or filesystem access.

## Start Codex And Invoke CAM

Start Codex inside the project you want CAM to help with:

```bash
cd /path/to/your/project
codex
```

Inside Codex, say:

```text
Use cam-codx-setup to verify CAM.
```

After that, ask for a CAM workflow:

```text
Use CAM_Codx to evaluate this repo and recommend next steps.
```

or:

```text
Use CAM_Codx to create a build plan for this repo.
```

When you are still deciding what to build or whether to rescue a work-in-
progress repository, start with the Development Brief instead of a build plan:

```text
Use cam-codx-development-brief to assess this repository and recommend continue, mitigate, or re-develop.
```

Codex will use CAM_Codx as the workflow guide and CAM_CAM as the runtime engine,
usually through commands shaped like:

```bash
~/CAM/scripts/cam-codx evaluate /path/to/your/project --mode structural
```

## Learn From The XTtape Showpiece

For a novice-friendly example, start with the XTtape showpiece:

- [XTtape case study](examples/XTTAPE_CAM_SHOWPIECE_CASE_STUDY.md)
- [XTtape comparison summary](showpieces/xttape-cam-comparison/COMPARISON_SUMMARY.md)
- [Final XTtape build brain](showpieces/xttape-cam-comparison/runs/final/)
- [Next implementation plan](showpieces/xttape-cam-comparison/docs/plans/2026-06-25-xttape-live-ai-news-ticker.md)

The lesson is not that CAM_Codx automatically builds a better app. The lesson
is that CAM_Codx can improve the build contract before coding by recalling
useful methods, comparing a vanilla plan against a CAM-recall plan, and making
evidence gates explicit.

## Continue From A CAM Packet

Repo Necromancer packets generated by CAM_CAM commonly include:

- `CAM_CODEX_GOAL.md`
- `NECROMANCER_SHOWPIECE.md`
- `evidence.json`
- optional demo files under `fused_app/`

In Codex, start from the generated goal:

```text
/goal /path/to/packet/CAM_CODEX_GOAL.md
```

If `/goal` is unavailable, paste the file contents and tell Codex to treat it
as the active completion contract.

## Keep Packet And Product Separate

A packet is source evidence and a build handoff. A standalone repo is the
product. For Repo Necromancer work, success usually requires a real standalone
repo with runtime code, tests, README, provenance, and a smoke command.

For planning showpieces like XTtape, the artifact bundle is the proof of the
planning workflow. It is not the finished product app. The next step is to
execute the saved implementation plan into a separate product repo.

## Local Config

Copy the public examples under `templates/config/` into local-only config files
and replace placeholders with your own paths and keys. Do not commit local
`.env` files, private endpoints, local databases, or real API keys.

For a full clean-machine setup with validation checkpoints, use
[`NEW_COMPUTER_SETUP_WALKTHROUGH.md`](NEW_COMPUTER_SETUP_WALKTHROUGH.md).
