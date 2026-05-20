# Codex-CAM Methodology — Implementation Handoff (Phase 4 Complete)

> Resume point after completing Phase 4. Two recall+provenance handlers landed; the surface ceiling test is still red (turns green in Phase 6 Task 6.3 when all 4 handlers register).

**Worktree:** `/Volumes/WS4TB/WS4TBr/CAM_Codx/codex-cam-methodology-impl` (branch `feature/initial-impl`, pushed to `origin/feature/initial-impl` on https://github.com/deesatzed/CAM_Codx)

**Branch HEAD:** `89f231e` (18 commits ahead of `main`)
**main HEAD:** `ec014b1` (untouched)

---

## What's done

### Phases 0, 1, 2, 3, 4 — ALL COMPLETE

| Phase | Status | Key artifacts |
|---|---|---|
| 0 Preconditions | ✅ (1 waiver) | manifest, RSS baseline, schema snapshot, failure-corpus waiver |
| 1 Scaffolding | ✅ | pyproject.toml, 11-file package skeleton, failing surface-ceiling test |
| 2 Schemas | ✅ | 10 pydantic v2 models in schemas.py (100% coverage, 12 tests) |
| 3 DB layer | ✅ | mode detection, frozen ModeInfo, read conn helper, asyncio write lock, idempotent outcome schema |
| 4 Handlers (recall + provenance) | ✅ | `handle_recall` (8 tests, 92% covered), `handle_provenance` (4 tests, 96% covered) |

### Test state at session end (38 passing tests, 1 expected red)

```
test_schemas.py          12 passed
test_fixture_db.py        2 passed
test_db_mode.py           4 passed
test_db_connections.py    8 passed
test_recall.py            8 passed (4 contract + 4 coverage-driven)
test_provenance.py        4 passed (3 contract + 1 link-exercise)
test_surface_ceiling.py   1 failed (expected RED until Phase 6 Task 6.3)
─────────────────────────────────────
TOTAL                    38 passed, 1 failed
```

### Coverage table (all implemented modules, post-Phase 4)

| Module | Coverage |
|---|---|
| `schemas.py` | **100%** |
| `tools/provenance.py` | **96%** |
| `db.py` | **94%** (waiver: 6 sqlite_vec.load defensive branches unreachable without mock) |
| `tools/recall.py` | **92%** (waiver: 6 defensive parse/timestamp branches against malformed data) |
| `__main__.py` | 0% (Phase 7) |
| `server.py` | 0% (Phase 6.3 will land 4 tool registrations) |
| 3 empty stub modules | N/A |
| **TOTAL (implemented)** | **93%** — above the project `fail_under = 90` gate |

---

## Plan bugs caught + amended in this session (running total: 9)

Phase 4 added two new amendments via subagent honesty:

1. (Phase 0–3, previously) 7 amendments
2. **Amendment #8 — `_corpus_size` dict row_factory bug.** The plan's `handle_recall` installs a dict row_factory then called `_corpus_size` which did `cur.fetchone()[0]` → `KeyError: 0`. Fix: alias the count column (`SELECT COUNT(*) AS n`) and access via `row["n"] if isinstance(row, dict) else row[0]`.
3. **Amendment #9 — `_row_to_hit` snippet truncation off-by-one.** Truncated to `SNIPPET_TRUNC=240` then appended "…" producing 241 chars, violating the pydantic `Field(max_length=240)` constraint and causing every long-notes row to raise `ValidationError`. Fix: truncate to `SNIPPET_TRUNC - 1`.

All amendments and waivers in `docs/_decision_log.md`.

---

## Commits this session (Phase 4)

| SHA | Message |
|---|---|
| `9e268ec` | feat(recall): cam_recall handler + 2 plan bug fixes + coverage tests |
| `2a09208` | feat(provenance): cam_provenance handler with link resolution + standalone path |
| `89f231e` | test(provenance): add link-exercise test to lift coverage 89→96% |

Plus the Phase 4.4 ratification — no new commit; the gate test already existed from Phase 3.5 commit `cb80d1c`.

Plus the Phase 4.5 coverage re-measure — recorded in decision log.

---

## What's NOT done

### Phase 5: Decisions index (3 tasks)
| Task | What |
|---|---|
| 5.1 | Failing indexer test (`tests/codex_mcp/test_decisions_index.py`) + fixture `tests/fixtures/sample_decisions/` |
| 5.2 | Implement `decisions_index.py` (FTS5 builder + searcher) |
| 5.3 | Implement `cam_decisions_search` handler + test |

### Phase 6: cam_record_outcome (3 tasks — the flywheel centerpiece)
- 6.1 failing test, 6.2 implementation (write path, **100% coverage required on db.py write paths**)
- 6.3 update `server.py` to register all 4 tools → surface_ceiling turns green

### Phase 7: MCP wire-up via __main__.py (3 tasks)
### Phase 8: `.codex/config.toml` + `.codex/AGENTS.md` updates (outside this repo)
### Phase 9: 4 SKILL.md files + 1 rewrite (outside this repo)
### Phase 10: 6 E2E gates (Claims 0-6)

**Approximate remaining: 23 tasks.**

---

## How to resume — recommended path

Open a fresh session with the `executing-plans` skill and hand it this prompt:

> Resume execution at Task 5.1 of `docs/plans/2026-05-19-codex-cam-methodology-implementation-plan.md`. Phases 0, 1, 2, 3, 4 complete. Read `meta/HANDOFF_LATEST.md` first for full state and the 9 plan amendments. Read `docs/_decision_log.md` for corpus reality facts and open coverage waivers. Working in worktree at `/Volumes/WS4TB/WS4TBr/CAM_Codx/codex-cam-methodology-impl` on branch `feature/initial-impl`. Current test state: 38 passed, 1 failed (test_surface_ceiling is the expected red until Phase 6 Task 6.3). Honor all workspace policies: NO MOCK, NO PLACEHOLDER, NO SIMULATION, NO TIMEFRAMES, NO COST/REVENUE, NO "production ready", validation gates between every step.

### Pre-flight checks

```bash
cd /Volumes/WS4TB/WS4TBr/CAM_Codx/codex-cam-methodology-impl
pwd && git status --short && git log --oneline -5
pytest tests/codex_mcp/ -q      # → 38 passed, 1 failed
```

### What the next implementer needs to know about Phase 5

1. **The `decisions_index.py` module is an empty stub** — it will own a new SQLite FTS5 index over `DECISIONS.md` files. This index is **separate from `claw.db`** (lives at `codex_decisions_index.db` in the configured path).

2. **The `tools/decisions_search.py` handler reads from this index, not from `claw.db`.** This is the one tool that works fully in standalone mode (zero CAM_CAM dependency).

3. **Phase 5 creates `tests/fixtures/sample_decisions/`** — small fixture directory tree with 2-3 fake `DECISIONS.md` files to exercise the indexer. Per build_specs.md §3.3, these are real DECISIONS.md files (just synthetic content), not mock data. Confirm if there's any sensitivity to that framing before dispatching.

4. **Watch for similar plan bugs to the ones we hit:** the plan's snippet for `decisions_index.py` may have similar SQL pattern issues. The implementer should run the indexer against the sample fixture and capture real output before trusting the spec.

5. **`db.py` and `tools/recall.py` have open waivers** at 94% and 92%. The plan said "re-measure at end of Phase 4" — done in Task 4.5. The branches are unreachable without mocks. At end of Phase 6, switch to `# pragma: no cover` with `# why:` comments per workspace policy "genuinely unreachable" rule. Documented in decision log.

---

## File inventory snapshot

```
src/claw_codex_mcp/
├── __init__.py                "0.1.0"
├── __main__.py                stub (Phase 7)
├── server.py                  REGISTERED_TOOLS = () (Phase 6.3)
├── schemas.py                 ✅ 10 pydantic models, 100% covered
├── db.py                      ✅ detect_mode, ModeInfo, open_read_conn, write_lock,
│                                 ensure_outcome_schema, 94% covered
├── decisions_index.py         stub (Phase 5)
└── tools/
    ├── recall.py              ✅ handle_recall + 6 helpers, 92% covered
    ├── provenance.py          ✅ handle_provenance, 96% covered
    ├── decisions_search.py    stub (Phase 5)
    └── record_outcome.py      stub (Phase 6)

tests/codex_mcp/
├── test_surface_ceiling.py    1 RED (expected; Phase 6.3)
├── test_schemas.py            12 GREEN
├── test_fixture_db.py          2 GREEN
├── test_db_mode.py             4 GREEN
├── test_db_connections.py      8 GREEN
├── test_recall.py              8 GREEN
└── test_provenance.py          4 GREEN

tests/fixtures/claw_slice.db   3.6 MB, 12 viable + 3 embryonic
migrations/001_codex_outcome_log.sql  ready for Phase 6
```

Working tree clean (after final commits). Branch pushed.

---

## Workspace policy compliance — verified clean

- **NO MOCK DATA** anywhere. All tests query the real slice DB or real tmp_path SQLite files.
- **NO TIMEFRAMES** in commit messages or docs.
- **NO COST/REVENUE** estimates.
- **NO "PRODUCTION READY"** claims; explicit phase status.
- **Validation gates** honored: every task verified before advancing; 9 plan bugs caught + amended.
- **Real APIs only**: pydantic 2.13.3, mcp 1.27.0, sqlite-vec 0.1.6, asyncio.Lock, all real and exercised.

Branch is **18 commits ahead of main**. None of those commits touch `main`. Merging to main is deferred until at least Phase 6 is complete (the centerpiece — closes the outcome ledger loop).
