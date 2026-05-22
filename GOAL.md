# GOAL.md

## Outcome

Run a Codex-CAM showpiece using `/Volumes/WS4TB/_MyGhRepos/mcp-cortex-handoff` as the source methodology corpus and update the Codex-CAM MCP implementation with one small, tested MCP-Cortex-inspired improvement.

The showpiece must prove that Codex-CAM can:

1. Mine a preliminary non-git source folder into CAM without fabricating corpus data.
2. Recall the newly mined MCP-Cortex methodology rows through `cam_cam`.
3. Cite provenance before editing Codex-CAM MCP code.
4. Apply one narrow MCP-Cortex pattern while preserving the four-tool MCP ceiling.
5. Verify the result locally.
6. Record the outcome through `cam_record_outcome`.
7. Log errors, fixes, evidence, and remaining risks.
8. Commit and push intentional repository updates.

## Source And Target

- Source methodology folder: `/Volumes/WS4TB/_MyGhRepos/mcp-cortex-handoff`
- Target implementation repo: `/Volumes/WS4TB/WS4TBr/CAM_Codx/codex-cam-methodology-impl`
- CAM infrastructure repo: `/Volumes/WS4TB/WS4TBr/CAM_Codx/CAM_CAM`

## Showpiece Direction

Use MCP-Cortex's compatibility-first policy/trace idea to improve Codex-CAM's existing MCP surface without adding tools.

Preferred narrow implementation:

- Keep exactly four MCP tools.
- Add deterministic Cortex-style invocation metadata to tool responses or outcome evidence only where it improves auditability.
- Do not add a policy engine or broad gateway rewrite.
- Preserve existing public CLI behavior and existing tests.

## Proof Of Done

1. Confirm starting repo states:
   - `git status --short --branch` in Codex-CAM implementation repo.
   - `git status --short --branch` in CAM_CAM.
   - Confirm `/Volumes/WS4TB/_MyGhRepos/mcp-cortex-handoff` has no `.git` and list its top-level files.
2. Run source-folder mining:
   - `cam mine-self --path /Volumes/WS4TB/_MyGhRepos/mcp-cortex-handoff --quick`
   - `cam mine-self --path /Volumes/WS4TB/_MyGhRepos/mcp-cortex-handoff`
3. Verify native recall/provenance:
   - Recall query: `mcp-cortex handoff policy trace intent capability deterministic MCP compatibility`
   - Use `k`, not `top_k`.
   - Use `include_embryonic=true`.
   - Call provenance for every methodology applied.
4. Implement one small Codex-CAM MCP update only.
5. Add focused tests for the update.
6. Run local verification:
   - Narrow changed tests.
   - `pytest tests/codex_mcp/ -q`
   - `python tools/product_smoke.py`
   - `git diff --check`
7. Record outcome through `cam_record_outcome` with:
   - methodology IDs used,
   - repo path,
   - commands and results,
   - stable run hash,
   - pass/fail status.
8. Update a tracked showpiece log under `docs/showpieces/`.
9. Commit and push intentional changes.

## Constraints

- Preserve the four-tool MCP ceiling.
- Do not add OpenRouter, xAI, Twilio, AWS, Docker, PostgreSQL, or external API requirements to Codex-CAM tests.
- Do not use mock, fake, placeholder, or copied corpus rows.
- Do not query CAM by direct sqlite for the showpiece proof once native recall is available.
- Do not modify `.codex/rules/default.rules`, secrets, credentials, private keys, `.env`, or generated databases except append-only outcome writes through `cam_record_outcome`.
- Do not weaken existing tests or delete assertions to pass.
- Keep CAM_CAM heavy engine behavior out of the inline Codex MCP path.

## Stop Conditions

Stop and summarize if:

- Mining the source folder requires unavailable credentials or external account changes.
- Native `cam_cam` recall cannot return newly mined MCP-Cortex rows.
- The narrow update would require adding a fifth MCP tool.
- Verification requires external services or credentials.
- The same failure persists after three distinct repair attempts.
- Any change would require committing secrets or unrelated dirty files.

## Completion Report

The final report must include:

- changed files,
- commands run and results,
- methodology IDs and provenance status,
- outcome row ID,
- commit hash,
- pushed branch,
- remaining risks or waivers.
