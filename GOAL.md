# GOAL.md

This is the source-of-truth completion contract for reorganizing the CAM repo
family into a professional, maintainable hub-and-spoke structure.

## OUTCOME

Make `CAM_Codx` the main public workflow hub for developers who use Codex, while
keeping `CAM_CAM` as the runtime/base engine and preserving generated products
such as `moriahcareframe` as separate standalone repos.

The finished structure should be easy to explain:

- `CAM_Codx`: Codex-native command center, goal templates, workflow docs,
  integration guides, examples, and professional front door.
- `CAM_CAM`: CAM runtime engine for mining, repo analysis, generators,
  dashboards, corpus handling, and tests.
- `moriahcareframe`: generated product repo proving the CAM/Codex workflow can
  create a standalone app.
- Claude Code and Grok Build: parallel adapter surfaces that consume CAM
  artifacts without changing the core repo ownership model.
- `CAM_ALL`: local clean operating workspace containing fresh GitHub clones
  under `repos/`, private runtime state under `local_state/`, scripts, and
  verification reports.
- `CAM_ARCHIVE`: local dated archive area for old duplicate folders, stale
  build artifacts, retired docs, and pre-cleanup snapshots.

## WHERE TO RUN THIS GOAL

Run this goal from the real Git-backed `CAM_Codx` checkout:

```bash
cd /Volumes/WS4TB/repo622sn/CAM_Codx
codex
```

Then, inside Codex, run:

```text
/goal GOAL.md
```

If `/goal` is not available in the current Codex surface, paste this instruction
instead:

```text
Use GOAL.md in /Volumes/WS4TB/repo622sn/CAM_Codx as the active completion
contract. Execute it exactly. Create CAM_ALL and CAM_ARCHIVE first. Do not
delete, move, rename, or archive old folders until the retirement manifest is
generated and explicitly approved.
```

Do not run this goal from:

- `/Volumes/WS4TB/WS4TBr/CAM_Codx`: this is a workspace/container folder, not
  the canonical GitHub-backed `CAM_Codx` checkout.
- `/Volumes/WS4TB/WS4TBr/CAM_Codx/CAM_CAM`: this is the runtime/base engine
  repo, not the hub repo.
- `/Volumes/WS4TB/WS4TBr/MoriahCareFrame`: this is a generated product repo,
  not the platform/workflow hub.

## PROOF OF DONE

1. `CAM_Codx` contains a polished `README.md` that clearly explains the
   hub-and-spoke model, who the repo is for, how it uses `CAM_CAM`, how
   generated product repos fit, and how Claude Code/Grok Build fit.
2. `CAM_Codx` contains these files:
   - `docs/ARCHITECTURE.md`
   - `docs/QUICKSTART_CODEX.md`
   - `docs/WORKFLOW_REPO_NECROMANCER.md`
   - `docs/examples/MORIAH_CAREFRAME_CASE_STUDY.md`
   - `docs/integrations/CLAUDE_CODE.md`
   - `docs/integrations/GROK_BUILD.md`
   - `docs/repo_inventory/CANONICAL_REPOS.md`
   - `docs/repo_inventory/LOCAL_FOLDER_AUDIT.md`
   - `docs/repo_inventory/RETIREMENT_MANIFEST.json`
   - `docs/STATUS.md`
   - `docs/FAQ.md`
   - `docs/REPO_MAP.md`
   - `templates/goals/repo-necromancer-standalone.md`
   - `templates/goals/cam-repo-audit.md`
   - `templates/goals/cam-generated-product-hardening.md`
   - `templates/claude-code/CLAUDE.md`
   - `templates/claude-code/repo-necromancer-handoff.md`
   - `templates/grok-build/BUILD_BRIEF.md`
   - `templates/grok-build/repo-necromancer-build-packet.md`
3. `CAM_CAM` links back to `CAM_Codx` as the Codex-native workflow hub and keeps
   ownership of runtime tools such as `scripts/repo_necromancer.py`.
4. Claude Code and Grok Build docs/templates define how those tools consume CAM
   packets, source receipts, and generated goals while preserving read-only
   source boundaries.
5. A repo/folder inventory exists and classifies duplicate or confusing local
   folders as `keep`, `archive_candidate`, `delete_candidate`,
   `needs_user_review`, or `do_not_touch`.
6. No old folders are deleted, moved, archived, or renamed during this goal.
   Cleanup is only planned in `RETIREMENT_MANIFEST.json`.
7. Verification commands are run and recorded in
   `docs/reports/CAM_REPO_REORG_VERIFICATION_2026-06-21.md`.
8. Configuration and database alignment is documented and verified:
   - `docs/config/LOCAL_CONFIG_ALIGNMENT.md` maps the local runtime-critical
     files, including `CAM_CAM/data/claw.db`, `CAM_CAM/claw.toml`,
     `CAM_CAM/claw_cheap.toml`, `CAM_CAM/claw_grok.toml`,
     `CAM_CAM/.env.example`, and any Codex/Claude/Grok adapter config files.
   - `docs/config/GITHUB_SAFE_CONFIG_GUIDE.md` defines which config files are
     safe to publish, which must be templated, which must stay local, and how a
     new user should create their own local config.
   - `docs/config/CONFIG_DRIFT_CHECKS.md` records commands for comparing local
     runtime config against GitHub-safe templates without exposing secrets or
     copying local databases.
   - `CAM_CAM/data/claw.db` is treated as a local runtime database and is not
     copied into `CAM_Codx` or committed to GitHub.
9. Local workspace overlay exists and is documented:
   - `/Volumes/WS4TB/CAM_ALL/README_LOCAL.md`
   - `/Volumes/WS4TB/CAM_ALL/MANIFEST.json`
   - `/Volumes/WS4TB/CAM_ALL/repos/CAM_CAM`
   - `/Volumes/WS4TB/CAM_ALL/repos/CAM_Codx`
   - `/Volumes/WS4TB/CAM_ALL/repos/moriahcareframe`
   - `/Volumes/WS4TB/CAM_ALL/local_state/CAM_CAM/`
   - `/Volumes/WS4TB/CAM_ALL/local_state/CAM_Codx/`
   - `/Volumes/WS4TB/CAM_ALL/local_state/adapters/`
   - `/Volumes/WS4TB/CAM_ALL/scripts/verify-all.sh`
   - `/Volumes/WS4TB/CAM_ALL/scripts/check-config-drift.sh`
10. `CAM_ALL/local_state` contains local-only runtime state or documented
    placeholders for:
   - `CAM_CAM/data/claw.db`
   - `CAM_CAM/data/clawBU.db` if retained
   - `CAM_CAM/config/claw.local.toml`
   - `CAM_CAM/config/claw_cheap.local.toml`
   - `CAM_CAM/config/claw_grok.local.toml`
   - `CAM_CAM/env/.env`
   - `CAM_Codx/config/codex.local.toml`
   - adapter-local config for Claude Code and Grok Build
11. `CAM_ARCHIVE` exists with a dated, non-destructive staging structure and a
    manifest, but no old folders are moved there until the user approves the
    generated retirement manifest:
   - `/Volumes/WS4TB/CAM_ARCHIVE/README.md`
   - `/Volumes/WS4TB/CAM_ARCHIVE/2026-06-21-pre-cleanup/MANIFEST.json`
12. GitHub repos are cleaned toward the clone-and-run standard:
   - keep source, tests, essential app docs, README, guide docs, landing page,
     templates, and safe examples,
   - remove or archive old build artifacts, stale generated outputs, dated
     reports, local transcripts, `.DS_Store`, `.pytest_cache`, and local-only
     config from tracked GitHub state,
   - no private runtime state is committed to GitHub.
13. Run these commands successfully where applicable:

```bash
cd /Volumes/WS4TB/repo622sn/CAM_Codx
git diff --check

cd /Volumes/WS4TB/WS4TBr/CAM_Codx/CAM_CAM
python -m pytest -q tests/test_repo_necromancer.py
git diff --check

cd /Volumes/WS4TB/WS4TBr/MoriahCareFrame
PYTHONPATH=src python -m pytest -q
sh scripts/smoke.sh
git diff --check
```

14. Final response includes:
   - repos touched,
   - commits created,
   - commands run and results,
   - GitHub URLs,
   - remaining dirty files,
   - local-only config/database files that were intentionally not committed,
   - `CAM_ALL` path and local-state summary,
   - `CAM_ARCHIVE` path and archive/cleanup status,
   - cleanup recommendations,
   - explicit statement that no destructive cleanup was performed.

## SCOPE

Canonical repo paths:

- `CAM_Codx`: `/Volumes/WS4TB/repo622sn/CAM_Codx`
- `CAM_CAM`: `/Volumes/WS4TB/WS4TBr/CAM_Codx/CAM_CAM`
- `MoriahCareFrame`: `/Volumes/WS4TB/WS4TBr/MoriahCareFrame`
- Clean local operating workspace: `/Volumes/WS4TB/CAM_ALL`
- Local archive workspace: `/Volumes/WS4TB/CAM_ARCHIVE`

Allowed modifications in `CAM_Codx`:

- `GOAL.md`
- `README.md`
- `docs/`
- `templates/`
- `PROGRESS.md`
- `DECISIONS.md`
- repo metadata docs required for professional presentation
- GitHub-safe config guides and templates under `docs/config/` and
  `templates/config/`
- docs and templates that explain `CAM_ALL` and `CAM_ARCHIVE`

Allowed modifications in `CAM_CAM`:

- docs that link runtime tools back to `CAM_Codx`
- Repo Necromancer user guide/docs
- GitHub-safe example config files such as `.env.example` or documented config
  templates when needed
- tests only if docs expose a real bug in generator behavior

Allowed modifications in `MoriahCareFrame`:

- docs or metadata needed to clarify that it is a generated product repo
- smoke/test docs if missing

Allowed modifications outside git repos:

- Create `/Volumes/WS4TB/CAM_ALL`
- Create `/Volumes/WS4TB/CAM_ARCHIVE`
- Create clean clones under `/Volumes/WS4TB/CAM_ALL/repos`
- Copy local-only runtime state into `/Volumes/WS4TB/CAM_ALL/local_state`
- Create wrapper scripts under `/Volumes/WS4TB/CAM_ALL/scripts`
- Create reports under `/Volumes/WS4TB/CAM_ALL/reports`
- Create archive manifests under `/Volumes/WS4TB/CAM_ARCHIVE`

Read/reference:

- all local CAM-like directories under `/Volumes/WS4TB`
- GitHub remotes for `CAM_Codx`, `CAM_CAM`, and `moriahcareframe`
- existing README, PRD, build specs, plans, and audits
- local runtime config files, including `claw.toml`, `claw_cheap.toml`,
  `claw_grok.toml`, `.env.example`, and `.codex/config.toml`
- local runtime database metadata for `CAM_CAM/data/claw.db`, using schema,
  table counts, file path, and documented purpose only; do not copy the DB
- current git status and recent commit history

Do not modify:

- old duplicate folders except to inventory them
- source repos used by generated product examples
- `.env`, credentials, API keys, tokens, private data, or local DB dumps
- `CAM_CAM/data/claw.db`
- local-only variants of `claw.toml` that contain machine-specific paths,
  private model choices, local endpoints, or secrets unless converted into a
  sanitized template
- unrelated projects under `/Volumes/WS4TB`
- old duplicate folders by moving, deleting, renaming, or editing them before
  the retirement manifest is generated and explicitly approved

## SAFETY / PROVENANCE

- Preserve the distinction between implemented behavior and planned behavior.
- Do not claim Claude Code or Grok Build integration is implemented unless it is
  verified by actual files and commands.
- Do not copy secrets, credentials, private keys, PHI, tokens, local databases,
  or sensitive data into docs or templates.
- Treat `claw.db` as a local runtime state artifact. Document how it is used and
  how a user can point to their own copy, but never publish the database.
- Separate local operational config from GitHub-safe generic templates. Public
  templates must use placeholders for keys, paths, models, and local endpoints.
- Treat source repos as read-only evidence unless a later goal explicitly
  scopes changes to those repos.
- Generated product repos must preserve source evidence and provenance.
- Cleanup planning is allowed; destructive cleanup is not allowed in this goal.
- `CAM_ALL/local_state` is the preferred home for local-only runtime files when
  it can be done without a broad rebuild. If direct relocation would require
  extensive code changes, use documented wrappers, env vars, ignored symlinks,
  or config flags as a transitional compatibility bridge.

## CONSTRAINTS

- Prefer hub-and-spoke over monorepo unless evidence proves a monorepo is safer.
- Keep `CAM_Codx` thin, professional, and workflow-focused.
- Keep `CAM_CAM` runtime-heavy and implementation-focused.
- Do not vendor CAM_CAM code into CAM_Codx.
- Do not duplicate generated product code in CAM_Codx.
- Do not add dependencies unless needed for verification and documented.
- Do not weaken tests or remove checks to make the goal pass.
- Do not invent GitHub state; verify remotes and branches with commands.
- Do not perform broad runtime rewrites just to relocate local state. Prefer a
  low-rebuild overlay using wrapper scripts and environment variables.
- Do not delete old files from GitHub repos until their role is classified as
  essential, archive, local-only, or obsolete.

## ITERATION

1. Confirm repo boundaries and remotes.
2. Inventory duplicate/confusing folders.
3. Create the `CAM_ALL` and `CAM_ARCHIVE` structure with manifests, but do not
   move or delete old folders yet.
4. Inventory local runtime config and database files, then define GitHub-safe
   generic templates and drift checks.
5. Fresh-clone GitHub repos into `CAM_ALL/repos`.
6. Copy local-only runtime state into `CAM_ALL/local_state` and create wrapper
   scripts that point repos at that state.
7. Update `CAM_Codx` positioning and architecture docs.
8. Add Codex goal templates.
9. Add Claude Code adapter docs/templates.
10. Add Grok Build adapter docs/templates.
11. Add backlinks from `CAM_CAM`.
12. Clean GitHub repos toward the clone-and-run standard after archive/local
   state manifests are complete.
13. Verify `moriahcareframe` remains a clean standalone generated product repo.
14. Write verification report.
15. Commit in small batches with clear messages.
16. Push touched canonical repos only after verification passes.

After each batch:

- run the nearest relevant verification,
- update `PROGRESS.md`,
- do not expand scope while verification is red.

## STOP

Stop and summarize before continuing if:

- the actual GitHub-backed checkout cannot be identified,
- git status shows user changes that would be overwritten,
- required verification cannot run,
- the task would require deleting/moving old folders,
- creating `CAM_ALL/local_state` requires broad runtime rewrites rather than
  wrappers/env/config bridge work,
- a repo contains sensitive data needed for inventory,
- config alignment would require exposing secrets, API keys, private local paths
  beyond safe placeholders, or publishing `claw.db`,
- a claim cannot be verified,
- the same failure repeats after 3 distinct mitigation attempts,
- a monorepo migration appears necessary rather than optional.

## COMPLETE

Mark complete only when:

- `CAM_Codx` is visibly the main workflow hub,
- `CAM_CAM` is visibly the runtime/base engine,
- Claude Code and Grok Build have equivalent adapter docs/templates,
- generated product repos are documented as separate outputs,
- duplicate/confusing local folders are inventoried and classified,
- `CAM_ALL` exists with clean clones, local state, scripts, and reports,
- `CAM_ARCHIVE` exists with a manifest and no destructive cleanup unless
  separately approved,
- runtime-critical local config and DB files are mapped to GitHub-safe templates
  or explicit local-only instructions,
- verification commands pass or failures are explicitly documented as unrelated,
- commits are created for all intentional changes,
- pushed branches match local commits,
- no destructive cleanup was performed.
