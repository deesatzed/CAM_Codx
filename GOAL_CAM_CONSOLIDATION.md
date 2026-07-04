# GOAL — CAM Consolidation: One Authoritative Version

**Created:** 2026-07-03
**Owner:** CAM_Codx (program-manager hub)
**Status:** COMPLETE (Tier 1 + Tier 2 executed 2026-07-03)
**Predecessor:** `GOAL_CAM_HYGIENE.md` (complete — 3 engine PRs merged; this goal picks up the drift it left behind)

---

## Purpose

After the hygiene goal, the **engine is clean and merged** but the local drive still holds
multiple divergent copies of CAM, an uncommitted config edit, and ~29 `claw.db` corpora with
no single declared "current" one. This goal establishes **exactly one authoritative version**
of each moving part — engine code, program-manager hub, config (`claw.toml`), and corpus
(`claw.db`) — and records that authority in-repo so any future run (CAM_Codx or manual) knows
what to use without re-deriving it.

**This goal does NOT** re-open WS5 (full CLI contraction) — that remains deferred future work.

---

## Ground Truth (verified 2026-07-03)

### Source-of-truth bindings (do not change without approval)
| Component | Authoritative location | Evidence |
|-----------|------------------------|----------|
| **Engine (`claw` pkg)** | `WS4TBr/CAM_Codx/CAM_CAM/src/claw` | Active `cam` (py313 env) editable finder resolves here |
| **Engine remote** | `deesatzed/CAM_CAM` `main` @ `b114d9a` | 0/0 vs origin; 0 open PRs; all 3 hygiene PRs merged |
| **Program-manager hub** | `repo622sn/CAM_Codx` | 0/0 vs origin |
| **Active CLI** | `/Users/o2satz/miniforge3/envs/py313/bin/cam` | `which cam` |

### Drift to resolve
1. **Data clone `repo622sn/CAM_CAM`** — **5 commits behind** `origin/main`, and carries
   **uncommitted working edits** never landed anywhere:
   - `claw.toml` (73-line diff: `db_path` fix `data/claw.db`→`claw.db`, 6 broken sibling
     ganglia commented out, profile-purpose header)
   - `claw_cheap.toml`, `claw_dspro.toml`, `claw_grok.toml` (6-line purpose headers each)
   - `RISK_NOTES.md` (16-line E-001 error-log correction)
   - Untracked: `claw.db.bak-20260629-062002`, `claw.db.bak-enrich-20260629-065251`,
     `mining_registry.json`
2. **Hub untracked handoff docs** — `HANDOFF_2026-07-02.md` + identical `HANDOFF_LATEST.md`
   (generated, never committed).
3. **~29 live `claw.db` corpora** across the drive with no declared "current." The largest and
   most recently mined is `repo622sn/CAM_CAM/claw.db` (~122 MB). `DB_REGISTRY.md` catalogs them
   but does not name a single authoritative live corpus.

---

## Workstreams

### WS-A — Declare the authoritative config (`claw.toml`)
The uncommitted `claw.toml` edits in the data clone are the *correct, intended* config
(verified last session), but they live only in an un-pushed working tree. The canonical engine
clone (`WS4TBr/.../CAM_CAM/claw.toml`) is the copy the running `cam` reads.

- **A1.** Decide the single authoritative `claw.toml`: reconcile the data-clone edits into the
  engine clone that `cam` actually reads, OR confirm the data clone is the run location. Record
  the decision in `DB_REGISTRY.md` / a new `CONFIG_REGISTRY.md`.
- **A2.** Ensure the four profiles (`claw.toml` active/glm, `_cheap`, `_dspro`, `_grok`) each
  carry their purpose header in the authoritative copy.
- **A3.** Verify all model IDs referenced in the authoritative `claw.toml` are in
  `APPROVED_MODEL_IDS` (`serial.py:36`). No unapproved model may ship in config.

**Done when:** one `claw.toml` per profile is declared authoritative, committed, and its models
are allow-listed.

### WS-B — Reconcile the data clone (`repo622sn/CAM_CAM`)
- **B1.** Commit the intended working edits (`claw*.toml`, `RISK_NOTES.md`) with a clear message,
  OR discard them if superseded by WS-A landing them in the engine clone. No silent stash.
- **B2.** Resolve the 5-commit `behind` — pull/rebase `origin/main` so the clone is `0/0`, or
  formally retire this clone as a pure corpus holder (not a code clone) in the registry.
- **B3.** Decide the fate of untracked artifacts (`claw.db.bak-*`, `mining_registry.json`) —
  gitignore, archive, or commit. State which and why.

**Done when:** `git status` on the data clone is clean and its role (corpus vs code) is declared.

### WS-C — Declare the authoritative corpus (`claw.db`)
- **C1.** Name the single **current live** `claw.db` in `DB_REGISTRY.md` (candidate:
  `repo622sn/CAM_CAM/claw.db`, ~122 MB, most-recently mined — confirm by content, not size alone).
- **C2.** Record what the running `cam` opens by default (from the authoritative `claw.toml`
  `db_path`) and confirm it points at the declared current corpus — no split brain between "what
  cam writes" and "what we call current."
- **C3.** Mark every other live `claw.db` in the registry with a role tag
  (backup / experiment / ganglion / empty / stale) so none is mistaken for current.

**Done when:** exactly one corpus is tagged CURRENT, and the running config demonstrably targets it.

### WS-D — Commit the handoff docs & this goal
- **D1.** Commit `HANDOFF_2026-07-02.md`; collapse or symlink `HANDOFF_LATEST.md` to avoid a
  duplicate drifting (they are byte-identical today).
- **D2.** Commit this `GOAL_CAM_CONSOLIDATION.md` to the hub.
- **D3.** Update `MEMORY.md` if any new source-of-truth fact was established.

**Done when:** hub `git status` is clean and pushed `0/0`.

---

## Definition of Done (two tiers — per operating rules)

### Tier 1 — Agent-owned (execute without gate)
- Reconcile / declare configs and corpus in-repo (WS-A analysis, WS-C tagging, doc writing).
- Produce commits locally; run `git status` verification.
- No fabricated estimates. No mock/placeholder corpora or configs. Real files only.

### Tier 2 — Human-gated (require explicit approval before executing)
- **Pushing** any repo to GitHub.
- **Discarding** any uncommitted edit or untracked `claw.db`/artifact.
- **Retiring/moving** any clone or corpus.
- **Rebasing/pulling** the data clone (rewrites its working state).

---

## Non-Goals
- WS5 full CLI contraction (deferred — see `WS5_CLI_REFACTOR_SPEC.md`).
- Deleting archived clones in `/Volumes/WS4TB/CAM_ARCHIVE/` (already reversibly archived by WS6).
- Any new engine feature work.

---

## Verification Checklist (completed 2026-07-03)
- [x] `claw.toml` authoritative copy declared + committed + models allow-listed (WS-A) —
      committed `9f389a6`→rebased `b96b59c`; all 7 active model IDs verified in `APPROVED_MODEL_IDS`
- [x] Data clone `git status` clean; role declared (WS-B) — RUN location + LIVE corpus holder;
      `claw.db.bak-*` + `mining_registry.json` gitignored; rebased to `0` behind
- [x] Exactly one `claw.db` tagged CURRENT; running config targets it (WS-C) —
      `repo622sn/CAM_CAM/claw.db` (2474 methods); `db_path="claw.db"` resolves to it from run dir;
      no split brain (engine clone's `data/claw.db` is a stale 2304-method snapshot)
- [x] Handoff docs committed; `HANDOFF_LATEST` de-duplicated (WS-D) — `HANDOFF_LATEST.md` is now
      a symlink → `HANDOFF_2026-07-02.md`
- [x] Data clone pushed (Tier 2); hub committed + pushed (Tier 2)
- [x] `DB_REGISTRY.md` records the authoritative binding (run location + config + CURRENT corpus)

## Outcome — the ONE authoritative version
| Layer | Authority |
|---|---|
| Engine code | `WS4TBr/CAM_Codx/CAM_CAM/src/claw` → `deesatzed/CAM_CAM` `main` |
| Program-manager hub | `repo622sn/CAM_Codx` → `deesatzed/CAM_Codx` `main` |
| Run location + config | `cd repo622sn/CAM_CAM && cam <cmd>` (uses local `claw.toml`, `db_path="claw.db"`) |
| CURRENT corpus (brain) | `repo622sn/CAM_CAM/claw.db` — 2474 methodologies |
