# Codex-CAM Methodology — Implementation Handoff (Phase 5 Complete)

> Resume point after completing Phase 5 (decisions index + cam_decisions_search). Three of the four MCP tools are now implemented; only `cam_record_outcome` and the server registration step remain in Phase 6.

**Worktree:** `/Volumes/WS4TB/WS4TBr/CAM_Codx/codex-cam-methodology-impl` (branch `feature/initial-impl`, pushed to `origin/feature/initial-impl`)
**Branch HEAD:** `6ad8bd4` (22 commits ahead of `main`)
**main HEAD:** `ec014b1` (untouched)

---

## What's done

### Phases 0–5 — ALL COMPLETE

| Phase | Status | Key artifacts |
|---|---|---|
| 0 Preconditions | ✅ (1 waiver) | manifest, RSS baseline, schema snapshot, failure-corpus waiver |
| 1 Scaffolding | ✅ | pyproject.toml, 11-file package skeleton, failing surface-ceiling test |
| 2 Schemas | ✅ | 10 pydantic v2 models in schemas.py (100% coverage, 12 tests) |
| 3 DB layer | ✅ | mode detection, frozen ModeInfo, read conn helper, asyncio write lock, idempotent outcome schema |
| 4 Handlers (recall + provenance) | ✅ | handle_recall (8 tests, 92%), handle_provenance (4 tests, 96%) |
| 5 Decisions index + search | ✅ | build_index/search_index in decisions_index.py (3 tests, 93%), handle_decisions_search (2 tests, 92%) |

### Test state at session end (43 passing, 1 expected red)

```
test_schemas.py             12 passed
test_fixture_db.py           2 passed
test_db_mode.py              4 passed
test_db_connections.py       8 passed
test_recall.py               8 passed
test_provenance.py           4 passed
test_decisions_index.py      3 passed
test_decisions_search.py     2 passed
test_surface_ceiling.py      1 failed (expected red until Phase 6 Task 6.3)
────────────────────────────────────
TOTAL                       43 passed, 1 failed
```

### Coverage table (post-Phase 5)

| Module | Coverage |
|---|---|
| `schemas.py` | **100%** |
| `tools/provenance.py` | **96%** |
| `db.py` | **94%** (waiver: defensive sqlite_vec.load branches) |
| `decisions_index.py` | **93%** |
| `tools/decisions_search.py` | **92%** |
| `tools/recall.py` | **92%** (waiver: defensive parse/timestamp branches) |
| `__main__.py` | 0% (Phase 7) |
| `server.py` | 0% (Phase 6.3 will land 4 tool registrations) |
| `tools/record_outcome.py` | 0% (Phase 6.1/6.2) |
| **TOTAL (implemented)** | **~94%** |

---

## Plan bugs caught + amended (running total: 10)

Phase 5 added one new amendment:

10. **Amendment #10 — indexer must include anchor in FTS body.** Plan indexed only `body` content; test query "mock data" only matched the H2 anchor text in repo_b. The implementer correctly diagnosed (real FTS5 against real sample DECISIONS.md fixtures) and fixed: index `f"{anchor}\n{body}"` so the H2 heading text is searchable. Decision titles are typically the highest-signal target, so this is the semantically correct behavior anyway.

All 10 amendments and the 2 open coverage waivers are in `docs/_decision_log.md`.

---

## Commits this session (Phase 5)

| SHA | Message |
|---|---|
| `661e08b` | feat(decisions): FTS5 index builder + searcher; idempotent rebuild |
| `6ad8bd4` | feat(decisions_search): cam_decisions_search; degraded path when index missing |

---

## What's NOT done

### Phase 6: cam_record_outcome (3 tasks — flywheel centerpiece)
| Task | What |
|---|---|
| 6.1 | Failing test for `handle_record_outcome` (`tests/codex_mcp/test_record_outcome.py`) |
| 6.2 | Implement `handle_record_outcome` in `tools/record_outcome.py` (the only write path; **100% coverage required on db.py write paths per build_specs §8.4**) |
| 6.3 | Update `server.py` to register all 4 tools → **surface_ceiling test turns GREEN** |

### Phases 7–10 (~18 tasks)
- Phase 7: MCP wire-up via `__main__.py` (stdio server)
- Phase 8: `.codex/config.toml` + `.codex/AGENTS.md` updates (outside this repo)
- Phase 9: 4 SKILL.md files + 1 rewrite (outside this repo)
- Phase 10: 6 E2E gates (Claims 0–6)

---

## How to resume

Open a fresh session with `executing-plans` and hand it this prompt:

> Resume execution at Task 6.1 of `docs/plans/2026-05-19-codex-cam-methodology-implementation-plan.md`. Phases 0–5 complete. Three of the four MCP tools are implemented: cam_recall, cam_provenance, cam_decisions_search. Only cam_record_outcome remains (the write path, the flywheel centerpiece) plus server.py registration. Read `meta/HANDOFF_LATEST.md` first for full state and the 10 plan amendments. Read `docs/_decision_log.md` for corpus reality facts and open coverage waivers. Working in worktree at `/Volumes/WS4TB/WS4TBr/CAM_Codx/codex-cam-methodology-impl` on branch `feature/initial-impl`. Current test state: 43 passed, 1 failed (test_surface_ceiling is the expected red until Phase 6 Task 6.3). Honor all workspace policies: NO MOCK, NO PLACEHOLDER, NO SIMULATION, NO TIMEFRAMES, NO COST/REVENUE, NO "production ready", validation gates between every step.

### Pre-flight checks

```bash
cd /Volumes/WS4TB/WS4TBr/CAM_Codx/codex-cam-methodology-impl
pwd && git status --short && git log --oneline -5
pytest tests/codex_mcp/ -q      # → 43 passed, 1 failed
```

### What the next implementer needs to know about Phase 6

1. **Phase 6 is the only phase that writes the surface_ceiling test turning green.** Task 6.3 updates `src/claw_codex_mcp/server.py` to import the four handlers (`handle_recall`, `handle_provenance`, `handle_decisions_search`, `handle_record_outcome`) and register them as `ToolRegistration` entries in `REGISTERED_TOOLS`. Currently `REGISTERED_TOOLS = ()` — the empty tuple is what keeps the ceiling test red as a TDD signal. Importantly: server.py is the *only* place this registration happens; there's no other tracking surface to keep in sync.

2. **`build_specs.md` §8.4 requires 100% coverage on `db.py` write paths.** The write paths are `ensure_outcome_schema` (already 100% from Phase 3.5) and the new `cam_record_outcome` insert path. Phase 6.2 must hit 100% on the write code path including the duplicate-`run_hash` branch.

3. **The `cam_record_outcome` tool is mode-aware:**
   - Connected mode: writes to `claw.db.codex_outcome_log` (so CAM_CAM's bandit can ingest)
   - Standalone mode: writes to `~/.cam_codex_mcp/codex_outcome_log.db` (local-only)
   - The `write_lock()` from Phase 3.5 serializes writes per-process

4. **The 4th tool's idempotency is `UNIQUE(run_hash)` + `INSERT OR IGNORE`** — duplicate `run_hash` returns `{recorded: false, duplicate: true}` and writes nothing. The test must verify this (insert twice with same hash, count rows = 1).

5. **Coverage waivers from Phases 3.5 + 4.1 stay open** until end of Phase 6 per the action plan. If branches remain unreached, switch to `# pragma: no cover` with `# why:` per workspace policy "genuinely unreachable" rule.

---

## File inventory snapshot

```
src/claw_codex_mcp/
├── __init__.py                "0.1.0"
├── __main__.py                stub (Phase 7)
├── server.py                  REGISTERED_TOOLS = () (Phase 6.3 lands the registration)
├── schemas.py                 ✅ 10 pydantic models, 100%
├── db.py                      ✅ 94%; ensure_outcome_schema ready for Phase 6
├── decisions_index.py         ✅ 93%; build_index + search_index ready
└── tools/
    ├── recall.py              ✅ handle_recall, 92%
    ├── provenance.py          ✅ handle_provenance, 96%
    ├── decisions_search.py    ✅ handle_decisions_search, 92%
    └── record_outcome.py      stub (Phase 6.2)

tests/codex_mcp/
├── test_surface_ceiling.py    1 RED (turns green Phase 6.3)
├── test_schemas.py            12 GREEN
├── test_fixture_db.py          2 GREEN
├── test_db_mode.py             4 GREEN
├── test_db_connections.py      8 GREEN
├── test_recall.py              8 GREEN
├── test_provenance.py          4 GREEN
├── test_decisions_index.py     3 GREEN
└── test_decisions_search.py    2 GREEN

tests/fixtures/
├── claw_slice.db                       3.6 MB, 12 viable + 3 embryonic
└── sample_decisions/
    ├── repo_a/DECISIONS.md             2 blocks (SQLite WAL + retry middleware)
    └── repo_b/DECISIONS.md             1 block (mock-data prohibition)

migrations/001_codex_outcome_log.sql    ready for Phase 6 (mirror of OUTCOME_LOG_DDL in db.py)
```

Working tree clean. Branch pushed.

---

## Workspace policy compliance — verified clean

- **NO MOCK DATA** anywhere. The sample DECISIONS.md fixtures are real markdown authored for testing (not synthetic data passed to a mocked indexer). The slice DB is real corpus rows. Every test exercises real SQLite, real FTS5, real pydantic.
- **NO TIMEFRAMES** in commit messages or docs.
- **NO COST/REVENUE** estimates.
- **NO "PRODUCTION READY"** claims; explicit phase status.
- **Validation gates** honored: every task verified before advancing; 10 plan bugs caught + amended.

Branch is **22 commits ahead of main**. None touch `main`. Merging deferred until at least Phase 6 lands the centerpiece.
