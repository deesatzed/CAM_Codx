# Real Use Case Test Plan

## MVP Definition

The real-use-case MVP is not a browser app. It is a local Codex-CAM product loop that a Codex user can test against actual repository work:

1. recall a relevant CAM methodology or honestly report that no corpus is connected,
2. cite provenance before applying a methodology,
3. do a bounded coding or repo-analysis task,
4. run verification,
5. append the outcome so future recall can improve.

The local smoke command proves the transport and data contracts underneath that loop:

```bash
cd /Volumes/WS4TB/WS4TBr/CAM_Codx/codex-cam-methodology-impl
python tools/product_smoke.py
```

This smoke test uses the official MCP SDK over stdio, launches the real `python -m claw_codex_mcp --transport stdio` server, and does not require OpenRouter, xAI, separate API keys, or interactive Codex TUI tool approval.

## Pilot 1: Repo Recon With Recall And Citation

Purpose: verify that a repo-orientation task can use CAM recall and decision search before making claims.

Commands:

```bash
cd /Volumes/WS4TB/WS4TBr/CAM_Codx/codex-cam-methodology-impl
python tools/product_smoke.py
CODEX_HOME=/Volumes/WS4TB/WS4TBr/CAM_Codx/.codex codex
```

Manual Codex prompt:

```text
Use repo_recon on this repository. Before giving recommendations, use cam_decisions_search and cam_recall if available. Cite any methodology you apply with provenance and say when the corpus is absent.
```

Pass criteria:

- Codex lists or uses only the four-tool `cam_cam` MCP surface.
- Any applied methodology includes a provenance citation.
- If `cam_recall` is unavailable or absent, Codex says so instead of inventing rows.
- The repo map identifies real files and real validation commands.

Fail criteria:

- Codex references `claw_query_memory` or `claw_store_finding`.
- Codex fabricates methodology ids, corpus counts, or model availability.
- Codex treats local SDK smoke success as proof that interactive Codex approval has been solved.

## Pilot 2: Feature Implementation With Outcome Logging

Purpose: verify the full recall -> cite -> apply -> verify -> record loop during a small implementation task.

Commands:

```bash
cd /Volumes/WS4TB/WS4TBr/CAM_Codx/codex-cam-methodology-impl
python tools/product_smoke.py
pytest tests/codex_mcp/ -q
```

Manual Codex prompt:

```text
Make a small, scoped improvement in this repo. Before editing, recall and cite a relevant CAM methodology if connected. After verification, record the outcome with cam_record_outcome.
```

Pass criteria:

- The implementation touches only scoped files.
- Verification runs after the edit.
- `cam_record_outcome` writes an append-only row.
- Reusing the same `run_hash` reports duplicate instead of inserting a second row.

Fail criteria:

- Outcome recording updates or deletes an existing row.
- The task succeeds only by weakening assertions or using mock corpus data.
- The smoke runner or Codex task requires OpenRouter, a separate API key, or `--dangerously-bypass-approvals-and-sandbox`.

## Pilot 3: Rescue Ladder After Repeated Verification Failure

Purpose: verify the rescue workflow without pretending the failure corpus is mature.

Commands:

```bash
cd /Volumes/WS4TB/WS4TBr/CAM_Codx/codex-cam-methodology-impl
python tools/product_smoke.py
pytest tests/codex_mcp/ -q
```

Manual Codex prompt:

```text
If the same verification fails twice, use the rescue_ladder skill. Recall error-handling methodology if available, cite provenance, try one bounded mitigation, and record the final outcome.
```

Pass criteria:

- The second consecutive failure triggers a bounded rescue attempt.
- Any recalled error-handling methodology is cited before use.
- If the corpus has no relevant failure methodology, the run records a waiver/blocker instead of fabricating one.
- The final result is either a verified fix or a documented blocker with exact command evidence.

Fail criteria:

- Codex loops indefinitely after repeated failures.
- Codex invents failure-corpus evidence.
- Codex edits outside the requested scope to make the test pass.

## Evidence Capture Template

Copy this block into the current handoff or validation note for each real-use-case run:

```markdown
### Real Use Case Evidence

- Date:
- Repo:
- Branch:
- Pilot:
- Command(s):
- MCP mode: standalone / connected / degraded
- Tool surface:
- Methodology id(s) cited:
- Provenance evidence:
- Verification result:
- Outcome run_hash:
- Outcome DB path:
- Pass/fail:
- Blockers or waivers:
- Changed files:
```

## Required Local Gates

Run these before claiming the local product loop is ready for human pilot use:

```bash
cd /Volumes/WS4TB/WS4TBr/CAM_Codx/codex-cam-methodology-impl
python tools/product_smoke.py
python tools/demo_stdio.py --mode standalone
python tools/demo_stdio.py --mode connected
pytest tests/codex_mcp/ -q
python tools/validate_skill_frontmatter.py --dir ../.codex/skills
rg -n "claw_query_memory|claw_store_finding" ../.codex/skills
git diff --check
```

Expected notes:

- The `rg` command should return no matches and may exit with status 1.
- `product_smoke.py` writes temporary SQLite files under `/private/tmp/cam_codex_mcp_product_smoke` unless `--work-dir` is supplied.
- `demo_stdio.py` writes demo SQLite files under `/private/tmp/cam_codex_mcp_demo` unless `--demo-dir` is supplied.

## Known Blockers And Waivers

- Interactive Codex E2E remains separate from local SDK smoke if Codex still cancels MCP tool calls in non-interactive `codex exec`. A passing `product_smoke.py` run proves the MCP server and SDK transport, not full interactive Codex approval behavior.
- `x-ai/grok-build-0.1` is deferred under the subscription-only policy unless a future Codex account/provider discovery path verifies that exact slug. Do not silently substitute another model.
- OpenRouter and separate API keys are not required for this local product smoke path.
- Rescue-rate claims remain waived until real failure-corpus evidence exists. Do not synthesize failure examples to satisfy the gate.

## Safety And Provenance Policy

- No mock, fake, placeholder, simulated, or cached corpus rows.
- Standalone mode must return honest absent-corpus responses.
- Connected mode must use real SQLite corpus data, currently `tests/fixtures/claw_slice.db` for local verification.
- Applied methodologies require provenance before use.
- Outcome logging is append-only and idempotent by `run_hash`.
- Historical model or benchmark records stay historical; active defaults must not be rewritten as if they were old evidence.
