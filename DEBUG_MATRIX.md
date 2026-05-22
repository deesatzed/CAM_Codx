# DEBUG_MATRIX.md

## Symptom

The MCP-Cortex showpiece eventually completed, but the first attempts produced avoidable failures: command syntax mistakes, provider/DNS failure in a nested sandbox, mining into the wrong local database, native MCP recall not seeing fresh rows, a temporary output-schema mismatch, a closed MCP transport, and Git staging failure from a linked-worktree sandbox boundary.

This matrix records root causes, mitigations, and the mitigation tests run after the successful showpiece.

## Reproduction Steps

The failure sequence is documented in `docs/showpieces/2026-05-22-mcp-cortex-showpiece.md`.

Representative failed operations:

- `sed` path-formatting command failed with `bad flag in substitute command`.
- Full `cam mine-self` failed with OpenRouter DNS error in a restricted independent Codex sandbox.
- Full mining was first run from the implementation repo cwd, creating a local `data/` directory not used by the native `cam_cam` MCP.
- Native `cam_recall` returned no `mcp-cortex-handoff-self` rows until mining was rerun from the CAM_CAM repo.
- A temporary `CamRecordOutcomeOutput` field addition caused native `cam_record_outcome` response validation failure.
- The active native MCP transport then closed before outcome recording could finish.
- A prior independent run could not stage files because the linked worktree Git index lived outside its writable roots.

## Known Facts

- Final native MCP proof succeeded in a fresh independent Codex session.
- Final outcome ID: `b0dfe005-d8d6-4c05-8248-ff86fd854d93`.
- Applied methodology ID: `2d863aeb-e7a3-4c1d-bafb-b94033c60aa9`.
- The public MCP surface still exposes exactly four tools.
- `cam_record_outcome` now stores deterministic invocation metadata inside outcome evidence, not in the output schema.
- The unrelated transcript and CAM_CAM `.env.example` changes were preserved and not committed.

## Unknowns

- Whether Codex CLI will eventually remove the deprecated `[features].collab` warning or change feature-flag names again.
- Whether future subscription/provider network restrictions will differ by shell, sandbox, or account state.
- Whether CAM_CAM mining should eventually accept an explicit DB path to remove cwd sensitivity.

## Root Cause Matrix

| Root Cause | Likelihood | Evidence For | Evidence Against | Diagnostic Check | Mitigation 1 | Mitigation 2 | Mitigation 3 |
|---|---:|---|---|---|---|---|---|
| Nested sandbox blocked provider DNS/network for full mining | High | Full mining failed with `[Errno 8] nodename nor servname provided`; same source quick scan worked | Later full-access retry reached OpenRouter and mined findings | `cam doctor keycheck --live` from CAM_CAM | Run provider preflight before full mining | Use independent Codex with `danger-full-access` only for provider-dependent mining; do not use unsafe bypass flags | Log network/provider blockers as blockers, not CAM recall failures |
| Mining ran from the wrong cwd, writing rows to the wrong `data/claw.db` | High | First successful mining created implementation-repo `data/`; native MCP corpus size did not include new rows | CAM_CAM-backed rerun made native recall return all 10 fresh rows | Run quick mining from `/Volumes/WS4TB/WS4TBr/CAM_Codx/CAM_CAM` and then native recall | Always run `cam mine-self` from the CAM_CAM repo unless an explicit DB path is supported | Add the CAM_CAM cwd to showpiece goals and command templates | After mining, require native recall of the source tag before editing |
| Native MCP schema drift from changing output fields | High | `cam_record_outcome` rejected extra `invocation_digest` from an intermediate output-field attempt | Evidence-only metadata passed tests and product smoke | `pytest tests/codex_mcp/test_record_outcome.py -q` plus product smoke | Keep new audit metadata inside stored evidence unless public schema change is intentional | Add tests for canonical evidence metadata and idempotence | Run product smoke after any MCP schema/tool-handler change |
| Stale or closed native MCP transport after code/schema changes | Medium | `cam_record_outcome` and then `cam_recall` returned `Transport closed` after code was changed and a helper process was killed | Fresh independent Codex run restored recall, provenance, and record outcome | Fresh `codex exec` native MCP preflight | Start a new independent Codex session after MCP code/schema changes before final native proof | Treat `Transport closed` as a session/process-state failure, not corpus failure | Verify idempotent duplicate outcome with the same run hash instead of writing a second row |
| Linked worktree Git index was outside the nested sandbox writable roots | Medium | Earlier independent run reported Git index path under sibling worktree outside writable roots | Full-access independent run staged, committed, and pushed | `git status --short --branch`; `git rev-parse --git-dir` when needed | Use `danger-full-access` for independent commit/push when linked worktree metadata is outside cwd | Or let the parent session commit after native proof succeeds | Stage explicit files only |
| Command ergonomics caused copy/paste and argument errors | Medium | Prior attempts included heredoc prompt continuation, wrong Codex flag placement, `top_k` instead of `k`, and an empty `cam_recall` call | Final prompt with exact arguments completed | Short no-edit native preflight prompt | Put long prompts in files or one-line checked command templates | Include exact MCP argument names in GOAL.md (`k`, not `top_k`) | Prefer `codex -a never -s workspace-write exec ...` ordering when user runs manually |
| Query/corpus retrieval ambiguity can mask whether rows exist | Medium | Initial native recall after wrong-cwd mining returned older MCP rows, not fresh source rows | CAM_CAM-backed corpus returned fresh rows with same required query | Compare corpus size and returned source tags through native recall | Require source tag visibility before editing | Use a second recall query with source tag/title terms only as diagnostic | Do not apply methodology until provenance resolves the exact methodology ID |

## First Diagnostic To Run

Before any future showpiece edit:

1. `cam doctor keycheck --live` from `/Volumes/WS4TB/WS4TBr/CAM_Codx/CAM_CAM`.
2. `cam mine-self --path <source> --quick` from `/Volumes/WS4TB/WS4TBr/CAM_Codx/CAM_CAM`.
3. Fresh independent `codex exec` native MCP preflight:
   - `cam_recall` with the exact query and `k`.
   - `cam_provenance` for the intended methodology ID.
   - idempotent `cam_record_outcome` only after verification, or duplicate check if the run hash already exists.

## Minimal Safe Fix

For the next showpiece, use a two-stage run:

1. Mining/preflight stage from CAM_CAM cwd with provider preflight.
2. Independent native Codex stage from the target implementation repo after native recall confirms fresh source rows.

Do not edit target code until stage 2 returns a fresh native methodology ID and provenance record.

## Regression Tests Needed

Already covered locally:

- `tests/codex_mcp/test_record_outcome.py` verifies deterministic invocation metadata and idempotent run hashes.
- `tests/codex_mcp/test_stdio_integration.py` verifies MCP stdio exposure and calls.
- `tests/codex_mcp/test_product_smoke.py` verifies one-command standalone and connected smoke behavior.
- `tests/codex_mcp/test_surface_ceiling.py` verifies the four-tool ceiling.

Recommended future hardening:

- Add a small command template or checklist for independent showpiece runs so `k`, cwd, and provider preflight are not hand-retyped.
- Add a CAM_CAM-side guard or CLI option that prints the active DB path before full mining writes findings.

## Mitigation Tests Run

```text
pytest tests/codex_mcp/test_record_outcome.py -q
8 passed in 0.09s
```

```text
pytest tests/codex_mcp/test_stdio_integration.py tests/codex_mcp/test_product_smoke.py tests/codex_mcp/test_surface_ceiling.py -q
6 passed in 2.15s
```

```text
python tools/product_smoke.py
PASS version 0.1.0
PASS standalone tools cam_decisions_search,cam_provenance,cam_recall,cam_record_outcome
PASS standalone recall_absent corpus_status=absent
PASS standalone provenance_absent found=false
PASS standalone decisions_search results=1
PASS standalone outcome_idempotent outcome_db=/private/tmp/cam_codex_mcp_product_smoke/standalone/outcomes.db
PASS connected tools cam_decisions_search,cam_provenance,cam_recall,cam_record_outcome
PASS connected recall_real_rows bc3febf8-c84c-483d-8d91-ba12f03c4b66
PASS connected provenance_resolves bc3febf8-c84c-483d-8d91-ba12f03c4b66
PASS connected decisions_search results=1
PASS connected outcome_idempotent outcome_db=/private/tmp/cam_codex_mcp_product_smoke/connected/outcomes.db
PRODUCT SMOKE PASS work_dir=/private/tmp/cam_codex_mcp_product_smoke
```

```text
cam doctor keycheck --live
OpenRouter: ok
Live preflight passed.
```

```text
cam mine-self --path /Volumes/WS4TB/_MyGhRepos/mcp-cortex-handoff --quick
Project: mcp-cortex-handoff
Source files: 40
Total size: 79 KB
Primary language: python
Complexity: small
Primary domain: ai_integration
```

Fresh independent native Codex MCP preflight:

```text
cam_recall: corpus connected, 10 results, target methodology visible at rank 6
cam_provenance: found=true, source path src/mcp_cortex/trace.py
cam_record_outcome: recorded=false, duplicate=true, reason=duplicate run_hash
RCA mitigation test result: green/idempotent duplicate confirmed.
```

```text
git diff --check
pass
```

## If This Fails

If any future showpiece repeats the same blocker after the mitigations above:

1. Stop before editing.
2. Record the exact failing layer: provider preflight, mining cwd/DB, native recall visibility, native provenance, native outcome, verification, or Git write.
3. Start a fresh independent Codex session only if the failure is transport/session state.
4. Do not bypass native MCP proof with direct SQLite, JSON-RPC, copied DBs, or fabricated rows.
