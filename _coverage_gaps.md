# Coverage Gaps — claw_codex_mcp

**Last updated:** 2026-05-27  
**Overall coverage:** 78.91% (gate: ≥90% line + branch; 100% on write paths)

---

## GAP-CLAIM-5 — LIGHTNESS claim FAILS (HIGH — Claim 5 gate)

**Status:** OPEN — requires user waiver OR investigation and action plan  
**Measured:** new MCP RSS = 93,011,968 bytes; legacy 17-tool MCP RSS = 62,554,112 bytes; ratio = 1.49  
**Gate ceiling:** ratio ≤ 0.50 (new must be ≤50% of legacy)  
**Actual outcome:** new MCP is **1.49× HEAVIER** than legacy, not lighter  

**Root cause analysis:**  
The new thin 4-tool MCP server runs as a pure Python stdio subprocess. The legacy 17-tool server was also measured as a Python process. The new server imports the MCP SDK client layer + anyio + pydantic + sqlite3 bindings on every startup, which accounts for most of the baseline memory. The legacy measurement (`baselines/legacy_mcp_rss.txt`) was taken with `python -c "from claw.mcp_server import server; ..."` which only loaded the CAM_CAM module — a very lightweight measurement. The new server measurement includes a full MCP SDK session round-trip.

**Likely cause of asymmetry:** The legacy baseline may have been captured with a minimal import (not a full running server session), while the new measurement captures a real running server with SDK overhead. The comparison may not be apples-to-apples.

**Action plan:**
1. Re-capture the legacy baseline using the same methodology: start the legacy 17-tool server with `--transport stdio`, perform initialize + tools/list, measure RSS under `/usr/bin/time -l`.
2. If the legacy server can't be started (e.g., missing env), document the limitation and request a user waiver for the lightness claim.
3. If after re-measurement the ratio still exceeds 0.50, request user waiver with a note that the "thin librarian" thesis holds architecturally (4 tools vs 17) even if RSS is not lower due to Python SDK overhead.

**Blocked by:** User must decide: re-capture baseline OR grant waiver.

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
