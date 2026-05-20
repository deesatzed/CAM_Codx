# Codex-CAM Methodology — Implementation Handoff (Phase 3 Complete)

> Resume point after completing Phase 3 of the implementation plan.

**Worktree:** `/Volumes/WS4TB/WS4TBr/CAM_Codx/codex-cam-methodology-impl` (branch `feature/initial-impl`, pushed to `origin/feature/initial-impl` on https://github.com/deesatzed/CAM_Codx)

**Branch HEAD:** `d00800c` (15 commits ahead of `main`)
**main HEAD:** `ec014b1` (untouched)

---

## What's done

### Phases 0, 1, 2, 3 — ALL COMPLETE

| Phase | Status | Key artifacts |
|---|---|---|
| 0 Preconditions | ✅ (with 1 waiver) | manifest, RSS baseline, schema snapshot, failure-corpus waiver |
| 1 Scaffolding | ✅ | pyproject.toml, 11-file package skeleton, failing surface-ceiling test |
| 2 Schemas | ✅ | 10 pydantic v2 models in schemas.py (100% covered, 12 tests green) |
| 3 DB layer | ✅ | mode detection, frozen ModeInfo, read conn helper, asyncio write lock, idempotent outcome schema bootstrap, migrations/001_codex_outcome_log.sql |

### Test state at session end (all in `tests/codex_mcp/`)

```
test_schemas.py          12 passed     (schema validation; 100% coverage on schemas.py)
test_fixture_db.py        2 passed     (slice DB fixture exists + has populated provenance)
test_db_mode.py           4 passed     (detect_mode connected/standalone + ModeInfo frozen)
test_db_connections.py    8 passed     (read-only enforcement, write-lock serialization,
                                        idempotent schema, 3 defensive-path tests)
test_surface_ceiling.py   1 failed     (expected RED — REGISTERED_TOOLS empty until
                                        Phase 6 Task 6.3 wires the 4 handlers)
─────────────────────────────────────
TOTAL                    26 passed, 1 failed (expected red)
```

**Coverage:**
- `schemas.py`: **100%**
- `db.py`: **94%** (target ≥95%; coverage waiver recorded in `docs/_decision_log.md` — 6 uncovered statements are sqlite_vec.load() failure paths that require monkey-patching to exercise, violating the no-mock rule. Re-measure at end of Phase 4.)

---

## Commits this session (Phase 3)

| SHA | Message |
|---|---|
| `0027ca9` | test(fixtures): conftest + slice-DB existence check (currently SKIP) |
| `4368a98` | test(fixtures): real 15-row slice of claw.db built from live corpus |
| `956536f` | fix(fixtures): mix embryonic + viable in slice so files_affected is populated |
| `4471338` | docs(handoff): Phases 0+1+2 complete + Phase 3 partial |
| `a1d7304` | feat(db): mode detection (connected/standalone/degraded) — frozen ModeInfo |
| `cb80d1c` | feat(db): read-only conn helper, write lock, idempotent outcome schema |
| `d00800c` | fix(db): broaden _check_vec exception catch; add defensive-path tests |

---

## Plan bugs caught + amended in this session (running total: 7)

1. Task 0.4 — legacy `server` symbol not at module scope (was 1)
2. Task 0.5 — replay-identity unachievable (was 2)
3. Task 0.6 — zero real failures available (was 3, waived)
4. Task 3.2 — vec0 doesn't expose rowid; slice-size estimate wrong (was 4)
5. Task 3.2 + test_fixture_db — corpus reality: viable rows have empty `files_affected` (was 5)
6. Task 3.5 — `_check_vec` exception catch too narrow (caught OperationalError, missed DatabaseError) **NEW**
7. Coverage waiver — `db.py` at 94% not 95%; defensive sqlite_vec.load failure paths require mocking to exercise **NEW**

All amendments and waivers in `docs/_decision_log.md`.

---

## What's NOT done

### Phase 4: Handler implementations (5 tasks)
| Task | What |
|---|---|
| 4.1 | Failing `cam_recall` test |
| 4.2 | `cam_recall` handler implementation |
| 4.3 | Failing `cam_provenance` test |
| 4.4 | `cam_provenance` implementation |
| 4.5 | Phase 2 coverage check (re-measure db.py per the waiver) |

### Phase 5: Decisions index (3 tasks)
### Phase 6: cam_record_outcome (the flywheel centerpiece) (3 tasks)
### Phase 7: MCP wire-up via __main__.py (3 tasks)
### Phase 8: .codex/config.toml + .codex/AGENTS.md (3 tasks)
### Phase 9: 4 SKILL.md files + 1 rewrite (5 tasks)
### Phase 10: 6 E2E gates (Claims 0-6) (6 tasks)

**Approximate remaining: 28 tasks.**

---

## How to resume — recommended path

Open a fresh session with the `executing-plans` skill and hand it this prompt:

> Resume execution at Task 4.1 of `docs/plans/2026-05-19-codex-cam-methodology-implementation-plan.md`. Phases 0, 1, 2, 3 complete. Read `meta/HANDOFF_LATEST.md` first for full state and the 7 plan amendments. Read `docs/_decision_log.md` for corpus reality facts and the db.py coverage waiver. Working in worktree at `/Volumes/WS4TB/WS4TBr/CAM_Codx/codex-cam-methodology-impl` on branch `feature/initial-impl`. Current test state: 26 passed, 1 failed (test_surface_ceiling is the expected red until Phase 6 Task 6.3). Honor all workspace policies: NO MOCK, NO PLACEHOLDER, NO SIMULATION, NO TIMEFRAMES, NO COST/REVENUE, NO "production ready", validation gates between every step.

### Pre-flight checks

```bash
cd /Volumes/WS4TB/WS4TBr/CAM_Codx/codex-cam-methodology-impl
pwd  # → ...-impl
git status --short              # → empty
git rev-parse --abbrev-ref HEAD # → feature/initial-impl
git log --oneline -3            # → d00800c, cb80d1c, a1d7304
pytest tests/codex_mcp/ -q      # → 26 passed, 1 failed
```

### What the next implementer needs to know about Phase 4

1. **`db.py` provides 4 public helpers** ready for the handlers:
   - `detect_mode() -> ModeInfo` — call once at server startup
   - `open_read_conn(info) -> ContextManager[sqlite3.Connection]` — for `cam_recall` and `cam_provenance`
   - `write_lock() -> AsyncContextManager[None]` — for `cam_record_outcome`
   - `ensure_outcome_schema(db_path)` — idempotent bootstrap for the outcome log table

2. **The slice DB fixture** at `tests/fixtures/claw_slice.db` has 12 viable + 3 embryonic rows. **Only the 3 embryonic rows have populated `files_affected`.** Phase 4 handler tests that assert on provenance fields must account for this (e.g., query against embryonic rows specifically, or assert "at least one row has populated provenance").

3. **`sqlite_vec.load(conn)` is required** before any SQL that touches `methodology_embeddings`. The `open_read_conn` helper does this automatically when `info.vec_available=True`.

4. **`importlib.metadata.version("mcp")`** for SDK version reporting — `mcp.__version__` doesn't exist as an attribute.

5. **Plan errata to watch for in Phase 4:**
   - The plan's SQL examples in `build_specs.md` §3.1 are illustrative; the actual SQL in `tools/recall.py` may need to handle FTS5 syntax errors (`MATCH` against malformed queries).
   - The fitness scoring formula (`(success_count + 1) / (success_count + failure_count + 2)` — Laplace smoothing) must be implemented exactly per `build_specs.md` §3.5.
   - All output models carry a `corpus_status` field (Literal["connected", "empty", "absent", "degraded"]) — verify in tests.

---

## Open questions

1. PRD §8 Claim 3 amendment for the failure-corpus waiver (separate doc commit, deferred from Phase 0.6).
2. db.py coverage gap: re-measure at end of Phase 4; if still < 95%, switch to `# pragma: no cover` with explicit comments.
3. Codex CLI auto-fire trigger names — verify in Phase 9.
4. Phase 6.4 "Signal reaches CAM_CAM corpus" gate is connected-mode only; standalone mode writes to a local SQLite. The gate needs mode-aware splitting.

---

## File inventory snapshot

```
src/claw_codex_mcp/
├── __init__.py                "0.1.0"
├── __main__.py                NotImplementedError stub (Phase 7 Task 7.2 wires it)
├── server.py                  REGISTERED_TOOLS = () (Phase 6 Task 6.3 wires handlers)
├── schemas.py                 ✅ 10 pydantic v2 models, 100% covered
├── db.py                      ✅ detect_mode, ModeInfo, open_read_conn, write_lock,
│                                 ensure_outcome_schema, OUTCOME_LOG_DDL, 94% covered
├── decisions_index.py         docstring stub (Phase 5 implements)
└── tools/                     4 docstring stubs (Phase 4 + Phase 5 + Phase 6 implement)

tests/codex_mcp/
├── test_surface_ceiling.py    1 RED (expected; turns green Phase 6 Task 6.3)
├── test_schemas.py            12 GREEN
├── test_fixture_db.py          2 GREEN
├── test_db_mode.py             4 GREEN
└── test_db_connections.py      8 GREEN (5 contract + 3 defensive paths)

tests/fixtures/claw_slice.db   3.6 MB tracked binary, 12 viable + 3 embryonic
migrations/001_codex_outcome_log.sql  migration reference for future migrate-outcomes CLI
```

Working tree clean. Branch pushed.
