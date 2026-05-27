# Coverage Gaps — claw_codex_mcp

**Last updated:** 2026-05-27 (waiver granted for GAP-CLAIM-5)  
**Overall coverage:** 78.91% (gate: ≥90% line + branch; 100% on write paths)

---

## GAP-CLAIM-5 — LIGHTNESS claim (WAIVED — 2026-05-27)

**Status:** WAIVED by user  
**Waiver date:** 2026-05-27  
**Waiver scope:** Gate ceiling relaxed from ≤0.50 to ≤0.90 for this measurement context.  
**Measured (2026-05-27, apples-to-apples, both via full stdio initialize+tools/list handshake):**
- New thin MCP (4 tools, standalone): **94,781,440 bytes** (~90 MB)
- Legacy 17-tool CAM_CAM MCP: **108,986,368 bytes** (~104 MB)
- Ratio: **0.87** — PASSES under waived ceiling of ≤0.90

**Rationale accepted by user:** The "thin librarian" thesis holds architecturally — 4 tools vs 17, no CAM_CAM agent stack imported at startup. The ≤0.50 gate was written assuming the legacy server loaded its full agent stack (LLM clients, embedding engine) in stdio mode; it does not (lazy init). Both servers' dominant RSS cost is Python interpreter + MCP SDK (~80–90 MB regardless of tool count). The 13% saving is real and correct. End-user product behavior is identical whether the ratio is 0.87 or 0.50.

**Prior measurement error noted:** Original `legacy_mcp_rss.txt` was captured via a minimal Python import (62 MB), not a running server — that comparison was not apples-to-apples and has been replaced.

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

| ID | Gate | Measured | Ceiling | Waived ceiling | Date | Granted by |
|----|------|----------|---------|----------------|------|------------|
| GAP-CLAIM-5 | Claim 5 LIGHTNESS ratio | 0.87 | ≤0.50 | ≤0.90 | 2026-05-27 | User (explicit) |

---

## Resolution target

All gaps must be resolved or formally waived before **Phase 9 (verify_claim scripts)** begins. Phase 9 scripts test end-to-end behavior; the coverage gate must be green before behavioral claims can be asserted.
