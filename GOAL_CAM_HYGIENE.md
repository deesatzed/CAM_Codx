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

### WS3 — Make data self-documenting (P1, Goal-2)
- [ ] Adopt naming convention: live=`claw.<profile>.live.db`, backup=`claw.<profile>.backup-YYYYMMDD-HHMMSS.db`, experiment=`claw.<profile>.exp-<slug>.db`; ganglia stay `instances/<brain>/claw.db`.
- [ ] Create `CAM_Codx/DB_REGISTRY.md`: one row per `claw.db` — path, purpose, owning_repo, profile, status (live/backup/exp/ganglion), created_by, last_used, notes. Seed from this session's audit.
- [ ] Add a header comment block to each `claw_*.toml` stating purpose, model set, when to use, and target `db_path`.
- **Done when:** every `claw.db` on the drive has a registry row and every toml has a purpose header.

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
- [ ] **P2 (real bug):** Fix `cam enrich --include-ganglia` in the ENGINE clone:
  `DatabaseEngine(DatabaseConfig(db_path=str(path)))` → `await connect()` →
  `await apply_migrations()` (replaces non-existent `g_engine.initialize()`).
- **Done when:** `enrich --include-ganglia` runs without `'DatabaseEngine' object has no
  attribute 'initialize'`. (Read-only-command item closed: no fix needed.)

### WS5 — Contract the CLI surface (P2, Goal/CLI)
Target ~10 top-level verbs + tight groups (full analysis: `CAM_Codx/CAM_CLI_ASSESSMENT.md`).
- [ ] Collapse `mine` / `mine-workspace` / `mine-all` / `mine-self` / `mine-report` into a `mine` group.
- [ ] Move `status`→`doctor status`, `stats`→`kb stats`, `gaps`→`kb gaps`; drop duplicate top-level `benchmark` (keep `forge benchmark`).
- [ ] Stop double-exposing the 14 hidden top-level commands AND their grouped aliases; keep the group form canonical.
- [ ] Standardize `--config` across all corpus-touching commands (missing on kb/security/cag/learn).
- [ ] Reconcile/merge `evaluate` vs `camify`; document the distinction if kept separate.
- [ ] Review `preflight`'s "estimate time/budget" wording against the standing rule forbidding time/cost estimates.
- [ ] Confirm-or-hide research surfaces: `chat`, `ab-test`, `evolution`, `federate`.
- **Done when:** `cam --help` shows a contracted, grouped surface with no duplicate aliases and consistent `--config`.

### WS6 — Drive reorganization (P2, Goal-3; after WS1)
- [ ] Capture dirty state on backup clones (`camcxBU64/CAM_CAM`, `buccx623/CAM_Codx`) before touching them.
- [ ] `mv` (never `rm`) the 7 fully-on-github stale clones into `/Volumes/WS4TB/CAM_ARCHIVE/<flattened-path>/`.
- [ ] Record a retention policy in `DB_REGISTRY.md` (when archived backups may be deleted).
- **Done when:** active tree = canonical engine + hub + data root; stale clones live under one archive dir; nothing deleted.

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

## Definition of Done (whole goal)

1. One canonical engine checkout, == GitHub, drives `cam`. ✅ already true; documented.
2. `repo622sn/CAM_Codx` unique work pushed; stray edit reverted.
3. `DB_REGISTRY.md` + naming convention + toml headers exist and are accurate.
4. `claw.toml` ganglion config clean; read-only commands exit 0; `enrich --include-ganglia` fixed.
5. CLI surface contracted and consistent.
6. Stale clones archived (moved) under one dir; nothing deleted; retention policy recorded.

---

## Reference Artifacts (this session)
- `CAM_CAM/HANDOFF_2026-06-29.md` — full state handoff.
- `CAM_Codx/CAM_ORG_PLAN.md` — repo/data reorg plan.
- `CAM_Codx/CAM_CLI_ASSESSMENT.md` — command-by-command CLI assessment.
- `CAM_CAM/RISK_NOTES.md` (E-001) + `failure_knowledge` row — mining reconcile false-positive.
