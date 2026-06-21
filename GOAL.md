# GOAL.md

This is the source-of-truth completion contract for the final CAM public-repo
cleanup pass. The prior reorganization proved the hub-and-spoke structure. This
goal makes the result durable enough to call "done forever" for a new user.

## OUTCOME

Make the public CAM repo family clean, current, cloneable, and explainable from
GitHub without relying on old local context.

When this goal is complete:

- `CAM_Codx` is the polished public workflow hub for Codex users.
- `CAM_CAM` is the runtime/base engine and contains only the public runtime
  surface, required tests, required docs, safe examples, and current showpieces.
- `moriahcareframe` remains a clean generated product proof repo.
- Claude Code and Grok Build are documented as adapter surfaces, not duplicated
  platform forks.
- `CAM_ALL` is the local operating overlay for clean clones and private runtime
  state.
- `CAM_ARCHIVE` records what was removed or kept out of GitHub.
- All status, verification, manifest, config, and README claims match current
  `origin/main` state.

## WHERE TO RUN THIS GOAL

Run from the canonical Git-backed `CAM_Codx` checkout:

```bash
cd /Volumes/WS4TB/repo622sn/CAM_Codx
codex
```

Then run inside Codex:

```text
/goal GOAL.md
```

If `/goal` is unavailable, paste this instead:

```text
Use /Volumes/WS4TB/repo622sn/CAM_Codx/GOAL.md as the active completion
contract. Execute it exactly. Treat CAM_Codx as the public hub, CAM_CAM as the
runtime engine, MoriahCareFrame as a generated product proof, CAM_ALL as the
local overlay, and CAM_ARCHIVE as the local archive. Do not delete local
workspace folders or local runtime state.
```

Do not run this goal from:

- `/Volumes/WS4TB/WS4TBr/CAM_Codx`: workspace/container folder.
- `/Volumes/WS4TB/WS4TBr/CAM_Codx/CAM_CAM`: runtime repo, not the hub.
- `/Volumes/WS4TB/WS4TBr/MoriahCareFrame`: generated product repo.

## PROOF OF DONE

1. Current-state docs are accurate:
   - `CAM_Codx` `README.md`, `docs/STATUS.md`, `PROGRESS.md`,
     `docs/reports/CAM_REPO_REORG_VERIFICATION_2026-06-21.md`,
     `docs/repo_inventory/LOCAL_FOLDER_AUDIT.md`, and
     `docs/repo_inventory/RETIREMENT_MANIFEST.json` contain current pushed
     commit heads, not stale `d5df0a5`, `287ed4a`, `7eec8bc`, or `40ba9f1`
     values unless explicitly labeled as historical.
   - `docs/STATUS.md` has no stale planned item saying cross-repo verification
     still needs to run after it has passed.
   - Final docs distinguish `verified`, `planned`, `historical`, and
     `local-only` state.

2. Public config claims are accurate:
   - `CAM_Codx/docs/config/GITHUB_SAFE_CONFIG_GUIDE.md` explicitly records that
     `CAM_CAM` currently tracks public-safe `claw.toml`,
     `claw_cheap.toml`, `claw_dspro.toml`, `claw_grok.toml`, and
     `.env.example` if that remains true.
   - Local-only config is limited to real secrets, local overrides, private
     endpoints, machine-specific paths, private `.env` files, and local DBs.
   - No doc claims all `claw*.toml` files are uncommitted if tracked public-safe
     defaults remain in GitHub.

3. GitHub repos meet the clone-and-run cleanliness standard:
   - `CAM_Codx` keeps only the hub source-of-truth surface: README, license,
     active docs, templates, repo inventory, status/progress/decision docs,
     active tools, and safe examples required for onboarding or verification.
   - `CAM_CAM` keeps only runtime code, package/build files, tests, current
     runtime docs, current guide docs, safe examples, and current showpieces.
   - `moriahcareframe` keeps only its app code, tests, README, smoke scripts,
     provenance docs, package metadata, and required generated proof artifacts.
   - Remove from tracked GitHub state, after classification, stale dated
     reports, obsolete handoffs, abandoned plans, old launch metrics, local
     transcripts, generated cache files, `.DS_Store`, `.pytest_cache`, old
     build outputs, and duplicate docs that conflict with the current story.

4. Cleanup is evidence-backed:
   - Create or update
     `docs/repo_inventory/PUBLIC_REPO_FILE_AUDIT_2026-06-21.md`.
   - Create or update
     `docs/repo_inventory/PUBLIC_REPO_CLEANUP_MANIFEST.json`.
   - Every removed tracked file is listed with repo, path, classification,
     reason, risk, and replacement/current source if any.
   - Every retained legacy-looking file has a reason.
   - Local folders under `/Volumes/WS4TB` are not deleted, moved, renamed, or
     archived by this goal.

5. `CAM_ARCHIVE` records cleanup provenance:
   - `/Volumes/WS4TB/CAM_ARCHIVE/README.md` explains the archive role.
   - `/Volumes/WS4TB/CAM_ARCHIVE/2026-06-21-public-cleanup/MANIFEST.json`
     records files removed from public GitHub tracking.
   - Archive records use paths, commit SHAs, and reasons. Do not copy secrets,
     private DBs, `.env` files, or sensitive local state into the archive.

6. `CAM_ALL` remains the local operating overlay:
   - `/Volumes/WS4TB/CAM_ALL/README_LOCAL.md` is current.
   - `/Volumes/WS4TB/CAM_ALL/MANIFEST.json` is current.
   - `/Volumes/WS4TB/CAM_ALL/local_state` contains placeholders or local-only
     files as intended, never committed into public GitHub repos.
   - `/Volumes/WS4TB/CAM_ALL/scripts/verify-all.sh` checks clean clones,
     `git diff --check`, expected files, and current remote heads.
   - `/Volumes/WS4TB/CAM_ALL/scripts/check-config-drift.sh` checks public-safe
     templates versus local runtime config shape without exposing secrets.

7. Fresh-clone proof exists:
   - Remove any stale clean-test clones used by this goal.
   - Fresh clone these remotes into a new proof directory under
     `/Volumes/WS4TB/CAM_ALL/clone_proofs/`:
     - `https://github.com/deesatzed/CAM_Codx.git`
     - `https://github.com/deesatzed/CAM_CAM.git`
     - `https://github.com/deesatzed/moriahcareframe.git`
   - Run the required verification commands from those fresh clones, not only
     from the working checkouts.
   - Record command output summaries in
     `docs/reports/CAM_PUBLIC_REPO_DONE_FOREVER_2026-06-21.md`.

8. Required commands pass from working checkouts:

```bash
cd /Volumes/WS4TB/repo622sn/CAM_Codx
git diff --check
python -m json.tool docs/repo_inventory/RETIREMENT_MANIFEST.json >/dev/null
python -m json.tool docs/repo_inventory/PUBLIC_REPO_CLEANUP_MANIFEST.json >/dev/null
python -m json.tool /Volumes/WS4TB/CAM_ALL/MANIFEST.json >/dev/null
python -m json.tool /Volumes/WS4TB/CAM_ARCHIVE/2026-06-21-public-cleanup/MANIFEST.json >/dev/null

cd /Volumes/WS4TB/WS4TBr/CAM_Codx/CAM_CAM
python -m pytest -q tests/test_repo_necromancer.py
git diff --check

cd /Volumes/WS4TB/WS4TBr/MoriahCareFrame
PYTHONPATH=src python -m pytest -q
sh scripts/smoke.sh
git diff --check

/Volumes/WS4TB/CAM_ALL/scripts/check-config-drift.sh
/Volumes/WS4TB/CAM_ALL/scripts/verify-all.sh
```

9. Required commands pass from fresh clones:
   - `CAM_Codx`: `git diff --check`, JSON/TOML/template validation, required
     docs/templates exist, no stale status references.
   - `CAM_CAM`: `python -m pytest -q tests/test_repo_necromancer.py` and
     `git diff --check`.
   - `moriahcareframe`: `PYTHONPATH=src python -m pytest -q`,
     `sh scripts/smoke.sh`, and `git diff --check`.

10. GitHub state is pushed and clean:
    - `git status --short --branch` is clean for `CAM_Codx`.
    - `git status --short --branch` is clean for `MoriahCareFrame`.
    - `CAM_CAM` is clean except for explicitly documented pre-existing local
      untracked files, or those files are moved out of the working checkout if
      safe and approved by manifest classification.
    - Local `HEAD` equals `origin/main` for every touched repo.
    - Final report lists exact commit SHAs and GitHub URLs.

11. Secret and local-state scan is clean:
    - Public repos do not track `.env`, local DBs, private keys, real API keys,
      private local adapter config, or machine-specific local-state files.
    - Any grep hits for `sk-`, `xai-`, `AIza`, `SECRET`, `TOKEN`, `PASSWORD`,
      or `API_KEY` are placeholders, environment variable names, or documented
      grep commands, and are recorded as false positives in the final report.

12. Final response includes:
    - repos touched,
    - commits created,
    - files removed from public GitHub state,
    - files intentionally retained despite legacy-looking names,
    - commands run and results,
    - fresh-clone proof path,
    - GitHub URLs and final SHAs,
    - remaining dirty/untracked local files,
    - local-only config/database files intentionally not committed,
    - confirmation that no local workspace folders were deleted, moved, or
      renamed.

## SCOPE

Canonical repo paths:

- `CAM_Codx`: `/Volumes/WS4TB/repo622sn/CAM_Codx`
- `CAM_CAM`: `/Volumes/WS4TB/WS4TBr/CAM_Codx/CAM_CAM`
- `MoriahCareFrame`: `/Volumes/WS4TB/WS4TBr/MoriahCareFrame`
- Local overlay: `/Volumes/WS4TB/CAM_ALL`
- Local archive: `/Volumes/WS4TB/CAM_ARCHIVE`

Allowed modifications in `CAM_Codx`:

- `GOAL.md`
- `README.md`
- `PROGRESS.md`
- `DECISIONS.md`
- `docs/`
- `templates/`
- `tools/`
- `.gitignore`
- removal of tracked files classified as obsolete, duplicate, stale, local-only,
  or misleading in `PUBLIC_REPO_CLEANUP_MANIFEST.json`

Allowed modifications in `CAM_CAM`:

- README and current public guide docs
- `docs/integrations/`
- `docs/showpieces/repo_necromancer/`
- `.gitignore`
- safe public config examples
- tests required to keep Repo Necromancer proof green
- removal of tracked files classified as obsolete, duplicate, stale, local-only,
  old build output, or misleading in the cleanup manifest

Allowed modifications in `MoriahCareFrame`:

- README, provenance docs, smoke docs, package metadata, `.gitignore`
- removal of tracked generated outputs only if they are not required for the
  smoke/test proof and are listed in the cleanup manifest

Allowed modifications outside git repos:

- `/Volumes/WS4TB/CAM_ALL/README_LOCAL.md`
- `/Volumes/WS4TB/CAM_ALL/MANIFEST.json`
- `/Volumes/WS4TB/CAM_ALL/scripts/`
- `/Volumes/WS4TB/CAM_ALL/reports/`
- `/Volumes/WS4TB/CAM_ALL/clone_proofs/`
- `/Volumes/WS4TB/CAM_ARCHIVE/README.md`
- `/Volumes/WS4TB/CAM_ARCHIVE/2026-06-21-public-cleanup/MANIFEST.json`

Read/reference:

- Current GitHub remotes for all three repos.
- Existing docs, plans, manifests, reports, README files, templates, and test
  commands.
- Local `CAM_CAM/data/claw.db` metadata only.
- Current tracked file lists from `git ls-files`.
- Current dirty state from `git status --short --branch`.

Do not modify:

- `/Volumes/WS4TB/WS4TBr/CAM_Codx` as a workspace/container folder except by
  operating inside its `CAM_CAM` child repo.
- Any old duplicate local folders under `/Volumes/WS4TB` by moving, deleting,
  or renaming them.
- `CAM_CAM/data/claw.db`, `CAM_CAM/data/clawBU.db`, private `.env` files, API
  keys, tokens, credentials, private local adapter configs, or private DB dumps.
- Source repos used as evidence for generated product examples.
- Unrelated projects under `/Volumes/WS4TB`.

## SAFETY / PROVENANCE

- Do not invent a cleaner state than commands prove.
- Do not remove tracked files until they are classified in the cleanup manifest.
- Do not delete local workspace folders. This goal may remove tracked files from
  GitHub repos after manifest classification; it may not delete local duplicate
  folders.
- Preserve provenance for generated product repos.
- Preserve `CAM_CAM` runtime behavior and tests.
- Keep local runtime state local. Use templates/placeholders for public setup.
- If a file may contain secrets or sensitive local data, stop and summarize
  before copying, archiving, or committing it.
- If a legacy-looking file is still useful for onboarding, current verification,
  or public explanation, keep it and document why.

## CONSTRAINTS

- Prefer a clean hub-and-spoke repo family, not a monorepo.
- Do not vendor CAM_CAM into CAM_Codx.
- Do not duplicate generated product code in CAM_Codx.
- Do not weaken tests or remove verification to make cleanup pass.
- Do not add dependencies unless needed for verification and documented.
- Do not rely on local-only state to prove a public clone works.
- Do not claim Claude Code or Grok Build runtime integration beyond documented
  adapter templates unless actual commands prove it.
- Keep public docs direct, current, and new-user oriented.
- Keep commit batches reviewable.

## ITERATION

1. Confirm current remotes, branches, heads, and dirty state for all three repos.
2. Generate tracked-file inventories with `git ls-files` for `CAM_Codx`,
   `CAM_CAM`, and `MoriahCareFrame`.
3. Classify files into `keep_public`, `move_to_archive_manifest`,
   `remove_from_public_git`, `local_only`, `needs_user_review`, or
   `do_not_touch`.
4. Stop for user review if any high-risk file would be removed from GitHub or if
   classification is ambiguous.
5. Update stale status, progress, report, and manifest commit references.
6. Correct config/local-state documentation so tracked public-safe defaults are
   not mislabeled as uncommitted local-only files.
7. Remove tracked stale/obsolete files from public GitHub repos only after the
   cleanup manifest records the reason and replacement/current source.
8. Update README/docs/templates so a new user sees a coherent first screen and
   clear next commands.
9. Update `CAM_ALL` scripts to verify clean clones, remote heads, expected files,
   and config drift.
10. Fresh-clone all three repos under `/Volumes/WS4TB/CAM_ALL/clone_proofs/`.
11. Run working-checkout verification.
12. Run fresh-clone verification.
13. Write `docs/reports/CAM_PUBLIC_REPO_DONE_FOREVER_2026-06-21.md`.
14. Commit in small batches.
15. Push touched repos.
16. Re-check local `HEAD == origin/main`, clean status, and fresh-clone proof
    after push.

After each batch:

- run the nearest relevant verification,
- update `PROGRESS.md`,
- keep dirty-state truth visible,
- do not expand scope while verification is red.

## STOP

Stop and summarize before continuing if:

- a required repo or remote cannot be verified,
- git status shows unrelated user changes that would be overwritten,
- a file proposed for removal may be current, sensitive, or high-risk,
- cleanup would require deleting, moving, or renaming local workspace folders,
- verification cannot run from a fresh clone,
- a public config appears to contain real secrets,
- `claw.db` or another local DB would need to be copied or committed,
- the same failure persists after 3 distinct mitigation attempts,
- the required cleanup would materially change product scope or repo ownership.

## COMPLETE

Mark complete only when:

- all stale status/report/manifest commit references are fixed or explicitly
  labeled historical,
- config documentation truthfully distinguishes tracked public-safe defaults
  from local-only overrides and secrets,
- public GitHub repos contain only classified, intentional files,
- cleanup manifests record every removed or retained legacy-looking file,
- `CAM_ALL` and `CAM_ARCHIVE` are current,
- working-checkout verification passes,
- fresh-clone verification passes,
- secret/local-state scan is clean or false positives are documented,
- final reports exist and match actual command output,
- commits are created for all intentional changes,
- local heads equal `origin/main` after push,
- final dirty state is documented,
- no local workspace folders were deleted, moved, or renamed.
