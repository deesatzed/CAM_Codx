# Coverage Gaps — claw_codex_mcp

**Last updated:** 2026-05-27  
**Overall coverage:** 78.91% (gate: ≥90% line + branch; 100% on write paths)

---

## GAP-COV-1 — `__main__.py` at 14% (HIGH — blocks CC.6 gate)

**Status:** OPEN — action plan written, not yet executed  
**Location:** `src/claw_codex_mcp/__main__.py` lines 26–200  
**Reason uncovered:** The stdio dispatch loop is exercised via subprocess in `test_stdio_integration.py` (MCP SDK `ClientSession` spawns a child process), so coverage.py cannot trace those lines in the subprocess's address space.  
**Write-path gate (CC.6 100%):** `db.py` and `tools/record_outcome.py` are both at **100%** — the write-path gate passes.  
**Remaining gap:** The gap is in the `__main__` entry-point glue (`_handle_request`, `_serve_stdio`, `_call_tool`, `_get_mode_info`, `main`).

**Action plan:**

1. Add `--cov-source=claw_codex_mcp` to pytest and use `coverage run --parallel` + `coverage combine` to merge coverage from the subprocess. Pytest-cov supports this via `--cov-append` if the subprocess is told to also instrument.
2. Alternatively, add direct unit tests for `_handle_request`, `_call_tool`, `_get_mode_info`, `_serve_stdio` by importing them directly and calling with mocked stdin/stdout — this is acceptable because these are pure dispatcher functions with no external side effects beyond the tool handlers (which are already tested separately).
3. The `# pragma: no cover` on the bare-exception handler at line 144 is intentional and documented — exclude it from the gap count.

**Blocked by:** None — can be resolved in Phase 9 prep before running verify_claim scripts.

---

## GAP-COV-2 — `decisions_index.py` at 93% (LOW — 7% below CC.6 gate)

**Status:** OPEN — 3 lines uncovered: 103, 116–117  
**Location:** `src/claw_codex_mcp/decisions_index.py:103,116–117`  
**Reason:** Edge-case branches in the FTS5 tokenizer and the re-index incremental logic.

**Action plan:**

Add two tests to `test_decisions_index.py`:
1. A test that triggers line 103 (the edge case in FTS5 snippet extraction — likely an empty-result branch).
2. A test that triggers lines 116–117 (the incremental-rebuild path with a file that was previously indexed but now has a different mtime or content hash).

---

## GAP-COV-3 — `tools/decisions_search.py` at 92% (LOW — line 23)

**Status:** OPEN — 1 line uncovered  
**Location:** `src/claw_codex_mcp/tools/decisions_search.py:23`  
**Likely cause:** An error-return branch when the index DB is unavailable or FTS5 returns a malformed result.

**Action plan:**

Add one test that exercises the uncovered branch (pass a query that triggers the error path — likely by pointing the tool at a nonexistent DB path or injecting a corrupt index fixture).

---

## Waiver log

No coverage waivers have been granted. All gaps have action plans.

---

## Resolution target

All gaps must be resolved or formally waived before **Phase 9 (verify_claim scripts)** begins. Phase 9 scripts test end-to-end behavior; the coverage gate must be green before behavioral claims can be asserted.
