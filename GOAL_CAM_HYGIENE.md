# GOAL_CAM_HYGIENE.md — CAM Source Control, Data Provenance & CLI Hygiene

**Created:** 2026-06-29
**Owner repo:** CAM_Codx (program-manager hub)
**Source of findings:** session audit on 2026-06-29 (handoff: `../CAM_CAM/HANDOFF_2026-06-29.md`).
**Scope note:** This is a HYGIENE/ORG goal, distinct from the product-feature goal in
`CAM_CAM/GOAL.md`. It does not change product features.

---

## Outcome

Make the CAM repo family, its data corpora, and its CLI **legible and trustworthy**:
one canonical engine on GitHub, every `claw.db`/`claw.toml` self-explaining, a clean
local drive, and a CLI surface that is grouped instead of sprawling — so that CAM_Codx
(or any human) can tell at a glance what exists, why, and which copy is real.

The driving question this goal answers: *"Which CAM do I run, which data is live, why
does each file exist, and why are there 60 commands?"*

---

## Why (problem statement)

This session surfaced four concrete, evidence-backed problems:

1. **Code/data split confusion.** The installed `cam` CLI runs from
   `/Volumes/WS4TB/WS4TBr/CAM_Codx/CAM_CAM` (== GitHub `f900dfc`), but work happens in
   `/Volumes/WS4TB/repo622sn/CAM_CAM` (5 commits behind, holds the live `claw.db`).
   Editing source in the working clone has no effect on the CLI — this caused a wasted
   fix attempt.
2. **Clone sprawl.** ~6 `CAM_CAM` + ~4 `CAM_Codx` clones and ~25 `claw.db` files across
   `/Volumes/{WS4TB,WS4TBr,CAMADA}`. After `git fetch`, **8 of 9 clones are fully on
   GitHub** (safe backups); only `repo622sn/CAM_Codx` holds unique unpushed work.
3. **Undocumented data.** No manifest says which `claw.db` is live vs backup vs
   experiment, or which `claw_*.toml` profile to use and why.
4. **CLI sprawl + a stale-config trap.** ~25 top-level commands + 12 groups with
   duplicate top-level/grouped aliases; several read-only commands appear "broken" only
   because `claw.toml` lists stale ganglion DBs lacking a `methodologies` table.

---

## Source Boundary (source of truth)

- **GitHub is canonical.** `deesatzed/CAM_CAM` (engine, `f900dfc`) and
  `deesatzed/CAM_Codx` (hub, `6fe47bf`).
- **Canonical local engine checkout:** `/Volumes/WS4TB/WS4TBr/CAM_Codx/CAM_CAM`
  (clean, == GitHub, drives the installed `cam`). Decision confirmed by user 2026-06-29.
- **Canonical hub working copy:** `/Volumes/WS4TB/repo622sn/CAM_Codx` (has the only
  unpushed work — must be pushed before archiving anything).
- **Live corpus:** `/Volumes/WS4TB/repo622sn/CAM_CAM/claw.db` (2,474 methodologies) +
  ganglia `repo622sn/instances/{typescript,rust}/claw.db`.
- Everything else under `/Volumes/*/CAM_*` is backup/experiment until proven otherwise.

---

## Workstreams & Tasks

### WS1 — Preserve unique work (P0, do first; nothing destructive until done)
- [x] Review dirty files in `repo622sn/CAM_Codx`; commit keepers. Agent-packs refresh validated (test_agent_packs.py 9/9) and committed as `3f973bf`; session hygiene docs committed as `2336db5`; stray `hist627.txt` shell-history dump gitignored (not committed).
- [ ] **Push** the 6 unpushed commits (4 prior + 2 new) to `deesatzed/CAM_Codx`. ← AWAITING HUMAN GO-AHEAD (outward action).
- [x] In `repo622sn/CAM_CAM`: reverted the stray `src/claw/cli/_monolith.py` edit; KEPT `RISK_NOTES.md` (E-001), `claw.toml` fix, `mining_registry.json`, corpus backups.
- **Done when:** `repo622sn/CAM_Codx` is `ahead=0` (needs push), working trees hold only intended changes (✅).

### WS2 — Lock the canonical engine (P1)
- [x] Confirmed `WS4TBr/CAM_Codx/CAM_CAM` == GitHub `f900dfc` (ahead=0 behind=0); editable install + `cam` resolve there. Stray `CAM_Codx_last5291pm.txt` (Claude Code TUI dump) gitignored, not deleted. One pending change: `.gitignore` +1 line (awaiting push approval).
- [x] Editable install stays pointed there. (Flat-path re-clone deferred; not required.)
- **Done when:** `import claw.cli._monolith` prints the WS4TBr path (✅) and engine tree is clean (✅, modulo the gitignore commit/push).

### WS3 — Make data self-documenting (P1, Goal-2) ✅ DONE
- [x] Naming convention documented in `DB_REGISTRY.md` (live/backup/exp/ganglion). Renames deferred (would touch live paths; convention recorded for future files).
- [x] Created `CAM_Codx/DB_REGISTRY.md` — all ~29 `claw.db` files cataloged with methods/size/mtime/status/why. Committed `52b8679`. Live = repo622sn/CAM_CAM/claw.db (2474).
- [x] Added purpose-header comment blocks to all 4 profiles: `claw.toml` (glm/active), `claw_cheap.toml`, `claw_dspro.toml`, `claw_grok.toml`. All parse-verified.
- **Done when:** every `claw.db` has a registry row (✅) and every toml has a purpose header (✅).

### WS4 — Fix the config trap + the one real bug (P1/P2)
- [x] **CORRECTION (2026-06-29):** The "read-only commands exit nonzero" finding was a
  **misdiagnosis** — `cam kb brains`/`learn report`/`doctor *` return **rc=0 when run
  directly** (verified: separate stdout/stderr, EXIT=0, full output). The earlier rc=2
  came from a **shell test-harness artifact** (`cam` as non-first command inside a `for`
  loop returns 2 under zsh job control). There was no command failure to fix.
- [x] **Real (cosmetic) finding kept:** the 6 configured sibling ganglia point at
  `multiclaw/*` DBs with no `methodologies` table, so federated commands print
  "Skipping <name>: no such table" NOISE (harmless). Disabled them in working-dir
  `claw.toml` (commented, reversible). NOTE: the running CLI loads the ENGINE's default
  `claw.toml` (`<engine>/claw.toml`), so fully removing the noise requires editing the
  engine config — deferred (touches the GitHub engine repo; low value).
- [x] **P2 (real bug) FIXED + VERIFIED:** `cam enrich --include-ganglia` now uses
  `DatabaseEngine(DatabaseConfig(db_path=...))` → `connect()` → `apply_migrations()`.
  On branch `fix/enrich-include-ganglia` (commit `ffc5173`) in the engine repo — NOT on
  main, NOT pushed. Verified: connects to rust+typescript ganglia and completes cleanly
  (was: `'DatabaseEngine' object has no attribute 'initialize'`).
- **Done when:** `enrich --include-ganglia` runs without the init error (✅). Remaining:
  merge branch → main + push (awaiting approval).

### WS5 — Contract the CLI surface (P2, Goal/CLI) — SPEC READY
Full old→new mapping written: `CAM_Codx/WS5_CLI_REFACTOR_SPEC.md` (back-compat aliases,
`--config` everywhere, `preflight` estimate-language removal). Ready to implement on
approval (engine branch). Tasks below are the spec's scope:
- [ ] Collapse `mine` / `mine-workspace` / `mine-all` / `mine-self` / `mine-report` into a `mine` group.
- [ ] Move `status`→`doctor status`, `stats`→`kb stats`, `gaps`→`kb gaps`; drop duplicate top-level `benchmark` (keep `forge benchmark`).
- [ ] Stop double-exposing the 14 hidden top-level commands AND their grouped aliases; keep the group form canonical.
- [ ] Standardize `--config` across all corpus-touching commands (missing on kb/security/cag/learn).
- [ ] Reconcile/merge `evaluate` vs `camify`; document the distinction if kept separate.
- [ ] Review `preflight`'s "estimate time/budget" wording against the standing rule forbidding time/cost estimates.
- [ ] Confirm-or-hide research surfaces: `chat`, `ab-test`, `evolution`, `federate`.
- **Done when:** `cam --help` shows a contracted, grouped surface with no duplicate aliases and consistent `--config`.

### WS6 — Drive reorganization (P2, Goal-3; after WS1) — SCRIPT READY (dry-run verified)
- [x] Archive script written + dry-run verified: `CAM_Codx/scripts/ws6_archive_clones.sh`.
  Captures dirty diffs to patches, REFUSES any clone with unpushed commits, moves never
  deletes, reversible. Re-verified the 7 clones are `ahead=0` on 2026-06-29.
- [x] Retention policy recorded in `DB_REGISTRY.md`.
- [ ] EXECUTE: `bash scripts/ws6_archive_clones.sh --execute` (awaiting approval; requires WS1 pushed first per guardrail).
- **Done when:** active tree = canonical engine + hub + data root; stale clones under `/Volumes/WS4TB/CAM_ARCHIVE/`; nothing deleted.

---

## Guardrails

- **No deletes.** Archiving = move only; deletion is a separate, later, explicit pass.
- **Push before archive.** Never archive a clone with unpushed/dirty work.
- **Fix in the engine clone.** Code changes belong in `WS4TBr/CAM_Codx/CAM_CAM`, not stale checkouts.
- **No time/cost/revenue estimates** anywhere in CAM output or docs (standing user rule); this includes the `preflight` review item.
- **Evidence over assumption.** Reconciles must union root + all `instances/*/claw.db`
  ganglia (a root-only check gave a false "38 lost" reading this session).

---

## Open Decisions (need human input)

- `<DATA_ROOT>` for the live corpus (default: keep in `repo622sn/CAM_CAM/`).
- Commit the 23 dirty `CAM_Codx` files as-is, or curate first?
- Archive destination (`/Volumes/WS4TB/CAM_ARCHIVE/`?) and retention window.
- Re-clone the engine to a flat path, or keep nested under `WS4TBr/CAM_Codx/`?
- CLI contraction: ship as breaking change, or keep hidden back-compat aliases with deprecation notes?

---

## Definition of Done

This goal has two tiers. **Engineering work** is what an agent can complete and verify
autonomously. **Human-gated release** covers outward, irreversible actions (publishing to
the public GitHub remote, refactoring the canonical engine, moving directories on disk)
that — per this goal's own Guardrails ("push before archive", "nothing destructive until
done") and the operator's standing rules — require explicit human authorization. An agent
must NOT perform Tier-2 actions to satisfy a checklist; doing so would violate the
guardrails this goal sets.

### Tier 1 — Engineering complete (agent-owned) ✅ DONE
1. Canonical engine identified, == GitHub `f900dfc`, drives `cam`; documented. ✅
2. `repo622sn/CAM_Codx` unique work committed locally; stray engine edit reverted. ✅
   (11 commits staged on the hub; engine `.gitignore` cleanup staged.)
3. `DB_REGISTRY.md` + naming convention + 4 toml purpose-headers exist and verified. ✅
4. Config trap diagnosed (false alarm — commands exit 0 directly); **real bug
   `enrich --include-ganglia` fixed and verified** on branch `fix/enrich-include-ganglia`. ✅
5. CLI contraction fully specified (`WS5_CLI_REFACTOR_SPEC.md`), ready to implement. ✅
6. Archive operation scripted and dry-run-verified (`scripts/ws6_archive_clones.sh`);
   retention policy recorded. ✅

### Tier 2 — Human-gated release (AUTHORIZED 2026-06-30, EXECUTED)
A. ✅ Pushed `CAM_Codx` to `deesatzed/CAM_Codx` (`6fe47bf..2b90fdf`). Rebased 8 new
   commits onto remote — the 4 base commits were already on remote under new SHAs;
   safety tag `pre-rebase-backup-20260630` kept.
B. ✅ Pushed engine branch `fix/enrich-include-ganglia` → **PR #1**
   (github.com/deesatzed/CAM_CAM/pull/1). Awaiting merge (human/CI gate).
C. ⚠️ PARTIAL — implemented the estimate-removal increment (preflight no longer
   fabricates time/cost; 18 tests pass) on `feat/cli-contraction` → **PR #2**. The full
   command-tree contraction (mine grouping, hidden-alias de-dup, `--config` coverage)
   remains specced in `WS5_CLI_REFACTOR_SPEC.md` — not yet implemented (larger refactor;
   deferred rather than half-done).
D. ✅ Executed `scripts/ws6_archive_clones.sh --execute`: 7 stale clones moved to
   `/Volumes/WS4TB/CAM_ARCHIVE/`, 2 dirty-state patches captured, canonical repos intact,
   nothing deleted.

**Goal status: Tier 1 complete. Tier 2 executed — A ✅, B ✅ (PR open), C ⚠️ partial
(increment merged-ready, full refactor deferred by scope), D ✅.**

### BLOCKER — PR merge gated on a model-governance decision (operator-only)
PRs #1 and #2 cannot merge green because engine `main` has a **pre-existing, unrelated
CI failure**: `tests/test_serial_evolution.py::TestApprovedModelConfig` fails because
`claw.toml` `fallback_models` lists two models absent from the `APPROVED_MODEL_IDS`
allowlist (`src/claw/evolution/serial.py:36`):
- `moonshotai/kimi-k2.7-code`  (likely intentional — cf. commit "route CAM mining through GLM and Kimi")
- `nvidia/nemotron-3-ultra-550b-a55b`

This is NOT caused by the agent's changes (reproduces on `main`). Per the standing rule
that **the operator selects all model versions**, the agent will not edit the allowlist or
the config to force CI green. **Operator decision required:**
- If these two models are APPROVED → add them to `APPROVED_MODEL_IDS` (serial.py:36). CI greens; PRs mergeable.
- If NOT approved → remove them from `fallback_models` in the 4 `claw.toml` profiles. CI greens.
(Separately: primary model `z-ai/glm-5.2` is also not in the allowlist, but is not in
`fallback_models`, so it does not trip this test — worth reviewing.)

Until this one-line, operator-owned decision is made, "merge PRs #1/#2 into canonical
`main`" cannot be completed without either shipping red CI or overstepping model
governance. This is a genuine human gate, not deferred agent work.

---

## Reference Artifacts (this session)
- `CAM_CAM/HANDOFF_2026-06-29.md` — full state handoff.
- `CAM_Codx/CAM_ORG_PLAN.md` — repo/data reorg plan.
- `CAM_Codx/CAM_CLI_ASSESSMENT.md` — command-by-command CLI assessment.
- `CAM_CAM/RISK_NOTES.md` (E-001) + `failure_knowledge` row — mining reconcile false-positive.
