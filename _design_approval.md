# Codex-CAM Methodology — Design Approval Record

**Approved by:** workspace owner  
**Approval date:** 2026-05-26  
**Evidence:** Implementation plan at `codex-cam-methodology-impl/docs/plans/2026-05-19-codex-cam-methodology-implementation-plan.md` (22 commits on `feature/initial-impl`; Phases 0–5 complete).  
**Note:** Sections 1–6 were approved implicitly when the `writing-plans` skill produced the implementation plan and execution began. This document closes the paper trail gap identified during the 2026-05-26 completeness audit.

---

## Section 1 — Architecture & Doctrine

- [x] Approved — 2026-05-26
- Three-plane architecture: Codex orchestrator ↔ thin librarian MCP ↔ CAM_CAM heavy engine (out-of-band)
- Boundary rule: Stateful + cross-repo + computational → MCP. Doctrine + workflow → Skill. Anything markdown-sized → Markdown.
- Hard 4-tool ceiling on new MCP server, enforced by CI surface-ceiling test.
- New thin MCP server (not a carve-out of the existing 17-tool server).

## Section 2 — MCP Surface

- [x] Approved — 2026-05-26
- Four tools: `cam_recall`, `cam_provenance`, `cam_decisions_search`, `cam_record_outcome`
- `cam_match_failure` deferred to v2 (failure_knowledge corpus too thin at time of design)
- `cam_record_outcome` is the sole write path; append-only, idempotent by `run_hash`
- Mode detection: `connected` / `standalone` / `degraded` — immutable per process lifetime

## Section 3 — Skill Bundle

- [x] Approved — 2026-05-26
- `cam_recall_and_cite` — new skill, auto-fires on recall; writes provenance line to `IMPLEMENT.md`
- `rescue_ladder` — new skill, auto-fires on 2nd consecutive verification failure
- `outcome_log` — new skill (flywheel centerpiece), auto-fires after any verified step that used a recalled methodology
- `repo_recon` — existing skill, modified to add `cam_decisions_search` call
- `deepscientist-data-research` — rewrite to use new 4-tool surface (phantom `claw_*` refs removed; `k=` → `limit=` fixed 2026-05-26)

## Section 4 — Doctrine Additions to `.codex/AGENTS.md`

- [x] Approved — 2026-05-26
- Four doctrine bullets to append verbatim:
  1. CAM_CAM is consulted as a librarian via MCP, never run inline.
  2. No mined methodology may be applied without its provenance row written to `IMPLEMENT.md`.
  3. On second consecutive verification failure, the `rescue_ladder` skill runs before the user is asked.
  4. After any verified step that used a recalled methodology, `outcome_log` must record the result.
- Updated doctrine tagline: "Codex decides. Claude contributes. Tests arbitrate. Markdown remembers. CAM librarian cites."

## Section 5 — Validation Plan

- [x] Approved — 2026-05-26
- Original 5 falsifiable claims (cold-start, provenance, failure-rescue, cross-project learning, lightness) + Claim 0 (MCP invoked at all)
- **Reframed 2026-05-26 (GAP-C2 resolution):** validation runs via Python MCP SDK directly, not through `codex exec`. Non-interactive Codex MCP approval is intentionally user-gated by OpenAI. Interactive E2E demo is manual gate M1, documented in `meta/VALIDATION_GAPS.md`.
- Five `tools/verify_claim_*.py` scripts to be built in Phase 10 against real `claw_slice.db` fixture.
- Baseline measurements on 5 unfamiliar repos captured in `baselines/` before methodology code landed (Phase 0 complete).

## Section 6 — Risk Register

- [x] Approved — 2026-05-26
- **Deferred to v2:** `cam_match_failure` tool (failure_knowledge corpus insufficient)
- **Deferred to v2:** HTTP transport for MCP (stdio-only in v1)
- **Out of scope for v1:** model-dispatch tools, daemons, silent pattern application above fitness threshold
- **Active risks carried forward:**
  - Secrets in `.codex/rules/default.rules` — separate remediation; this design must not require modifying that file until rotation complete
  - TypeScript corpus thin (2 viable methods at design time; mining in progress as of 2026-05-26)
  - `cam_record_outcome` write path must be 100% covered before any "learning" claim is valid (Phase 6 gate)
- **Mitigations in place:**
  - Surface-ceiling CI test enforces hard 4-tool limit
  - All tool responses include `corpus_status` field so skills can surface mode to user
  - `cam.silence(turn|session|repo)` escape hatch documented in skill frontmatter

---

## Checklist gate closure

This document satisfies gate **0.6** in `build_to_do_checklist.md`:

> Gate: a `_design_approval.md` file lists each section with a `[x]` and a date.
