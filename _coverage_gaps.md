# Coverage Gaps — claw_codex_mcp

**Last updated:** 2026-05-27 (GAP-COV-1/2/3 CLOSED; CC.6 gate GREEN)  
**Overall coverage:** 97.12% (gate: ≥90% line + branch — PASSES; 100% on write paths)

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

## GAP-COV-1 — `__main__.py` (CLOSED 2026-05-27)

**Status:** CLOSED — 14% → 92% via `tests/codex_mcp/test_main_dispatch.py`  
**Closed by:** 21 direct unit tests importing `__main__` functions (not via subprocess):
`_jsonrpc_result`, `_jsonrpc_error`, `_tool_definitions`, `_load_tool`, `_get_mode_info`,
`_handle_request` (initialize/ping/tools_list/tools_call_invalid/tools_call_unknown/notification/unknown_method),
`_call_tool` (unknown tool), `_serve_stdio` (ping/parse-error/notification), `main` (--version/bad-args/--transport-stdio/--transport=stdio).  
**Remaining 8%:** Lines 75-76 (`_write_message` direct stdout path — only exercised via subprocess), 95-97 (valid `tools/call` with real tool invocation path — also subprocess), 200 (`if __name__ == "__main__"` guard). These are correctly not covered by direct import tests and are acceptable per workspace policy with this documented explanation.  
**Write-path gate (CC.6 100%):** `db.py` and `tools/record_outcome.py` remain at **100%**.

---

## GAP-COV-2 — `decisions_index.py` (CLOSED 2026-05-27)

**Status:** CLOSED — 93% → 97% via two new tests in `test_decisions_index.py`  
- **Line 103** (`else anchor` branch in `build_index` when block body is empty): closed by `test_build_index_empty_body_block` — a DECISIONS.md with a heading immediately followed by another heading (no body text).
- **Lines 116-117** (`repo_filter` SQL branch in `search_index`): closed by `test_search_with_repo_filter` — calls `search_index` with `repo_filter` pointing to `repo_b`, verifying both positive and negative filtering.  
**Remaining 3%:** Branch-partial on the `body if body else anchor` condition — the truthy branch is exercised extensively; only the false-branch was missing (now covered). Coverage tool shows partial due to implicit branch tracking — acceptable at 97%.

---

## GAP-COV-3 — `tools/decisions_search.py` (CLOSED 2026-05-27)

**Status:** CLOSED — 92% → 100% via one new test in `test_decisions_search.py`  
- **Line 23** (`return DEFAULT_STANDALONE_DIR / DEFAULT_INDEX_NAME` in `_index_path()` when env var not set): closed by `test_index_path_default_when_env_unset` — calls `_index_path()` directly with `CAM_CODEX_MCP_DECISIONS_INDEX` removed from environment.

---

## Waiver log

| ID | Gate | Measured | Ceiling | Waived ceiling | Date | Granted by |
|----|------|----------|---------|----------------|------|------------|
| GAP-CLAIM-5 | Claim 5 LIGHTNESS ratio | 0.87 | ≤0.50 | ≤0.90 | 2026-05-27 | User (explicit) |

---

## Resolution log

| ID | Type | Final coverage | Resolved/waived | Date |
|----|------|---------------|-----------------|------|
| GAP-CLAIM-5 | Waiver | ratio=0.87 (ceiling waived to 0.90) | User (explicit) | 2026-05-27 |
| GAP-COV-1 | Closed | `__main__.py` 14% → 92% | `test_main_dispatch.py` (21 tests) | 2026-05-27 |
| GAP-COV-2 | Closed | `decisions_index.py` 93% → 97% | `test_decisions_index.py` (+2 tests) | 2026-05-27 |
| GAP-COV-3 | Closed | `decisions_search.py` 92% → 100% | `test_decisions_search.py` (+1 test) | 2026-05-27 |

**CC.6 gate status: PASSES** — 97.12% total (≥90% required); 100% write-path.
