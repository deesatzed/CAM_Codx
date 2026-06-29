# REVIEW.md

## Review Scope

- CAM_Codx hub checkout: `/Volumes/WS4TB/repo622sn/CAM_Codx`
- CAM_CAM runtime checkout: `/Volumes/WS4TB/WS4TBr/CAM_Codx/CAM_CAM`
- Local proof repos:
  - `/Volumes/WS4TB/CAM_ALL/repos/moriahcareframe`
  - `/Volumes/CAMADA/CAM_ALL/repos/MyLoc`
- Current CAM Agent Packs build, generated docs, smoke scripts, and repo-family
  verification commands.

## Summary Judgment

Needs Fixes before claiming this branch state is fully published. The build
passes the local verification commands, but CAM_Codx currently contains
uncommitted agent-pack documentation and smoke-script changes. Host pack smoke
scripts are syntactically valid, but not yet proven end-to-end inside real
target projects with CAM MCP configured.

## Findings

| Severity | Category | Finding | Why It Matters | Required Fix |
|---|---|---|---|---|
| P1 | Release readiness | CAM_Codx has intentional but uncommitted pack/docs/test changes. | `GOAL.md` requires a clean final repo state before completion. A green local tree is not a published artifact until committed and pushed. | Commit and push the uniform smoke-script/readme changes after final review. |
| P2 | Host verification | Claude, Gemini, and Grok smoke scripts are present and shell-valid, but not yet run in copied target projects with real CAM MCP config. | Syntax checks do not prove the host can call `claw_query_memory`; the docs correctly say not to claim end-to-end verification yet. | Create a disposable target project for each host, copy the pack, configure CAM paths, and save discovery/smoke receipts. |
| P2 | Cross-repo drift | CAM_Codx validates the contract internally, while CAM_CAM validates runtime schemas separately. No single test proves every contract tool name still exists in the live CAM_CAM tool registry. | The architecture depends on one contract mapping to a separate runtime repo. Split tests can miss cross-repo drift. | Add a cross-repo conformance check that compares `cam_agent_capabilities.json` tool names to CAM_CAM's registered MCP tools. |
| P2 | Proof repo management | MyLoc passes tests/smoke locally but has no configured remote/upstream in the checked repo. | A proof repo without a remote is harder to reproduce, publish, or include in aggregate verification. | Add a remote/upstream or document MyLoc as local-only; then include it in aggregate verification explicitly. |
| P3 | Operator UX | Pack setup is now uniform, but users still manually copy pack files and config examples. | Manual copy/merge is error-prone and will be repeated for every target project. | Add `tools/install_agent_pack.py` or a `cam-codx install-pack` command that copies one pack, refuses to overwrite secrets, and prints exact next commands. |

## Correctness

Local checks passed:

- CAM_Codx: `python -m pytest -q`, `python tools/generate_agent_packs.py --check`, `git diff --check`.
- CAM_CAM: `python -m pytest -q tests/test_tool_schemas.py tests/test_integration_wiring.py`, `git diff --check`.
- MoriahCareFrame: `PYTHONPATH=src python -m pytest -q`, `sh scripts/smoke.sh`, `git diff --check`.
- MyLoc: `sh scripts/smoke.sh`, `python -m pytest -q`, `git diff --check`.
- CAM_ALL aggregate: `/Volumes/WS4TB/CAM_ALL/scripts/verify-all.sh`.

The largest correctness gap is not failing tests; it is missing end-to-end host
pack proof after copying packs into real target projects.

## Security and Privacy

The latest targeted scan found no API key/private-key/local CAM DB path matches
in the CAM_Codx agent-pack surfaces. The generated examples keep real local
paths as placeholders, which is appropriate. Host smoke scripts should continue
to avoid permissive bypass flags and should not print secrets.

## Tests

CAM_Codx now has tests for uniform README sections, executable `smoke.sh`
scripts, generated output freshness, JSON config parsing, and basic no-secret
hygiene. Missing tests:

- Cross-repo CAM_Codx contract to CAM_CAM runtime registry conformance.
- Disposable target-project install/smoke tests for each host pack.
- Aggregate verification that includes MyLoc when MyLoc is considered a public
  proof repo.

## Maintainability

The generator-centered approach is the right maintenance decision. The next
maintenance step is to reduce manual install friction and add cross-repo drift
detection so CAM_Codx and CAM_CAM cannot silently diverge.

## Performance

No performance issue was found in the docs/generator layer. The generated pack
tests are fast, and the repo-family smoke checks are lightweight. End-to-end
host smoke tests may be slower because they invoke external agent CLIs; keep
them separate from the fast unit suite.

## UI/UX Impact

The landing README and generated pack READMEs now expose a uniform setup/test
path. The main UX gap is that setup still requires users to manually copy files,
merge JSON/TOML, replace placeholders, and know where to run discovery commands.

## Regression Risk

Regression risk is moderate and mostly documentation/runtime drift:

- Host docs can drift when Claude/Gemini/Grok CLI behavior changes.
- CAM_CAM tool names can drift from CAM_Codx contract entries.
- Manual pack installation can produce local configs that differ from examples.

## Scope Creep Check

The current uncommitted change is scoped to CAM_Codx generated pack docs,
smoke scripts, integration docs, tests, and progress tracking. CAM_CAM and
generated product repos were reviewed but not modified.

## Required Fixes Before Done

1. Commit and push the current CAM_Codx pack/docs/test changes if they are
   accepted.
2. Save host-pack end-to-end smoke receipts after installing each pack in a real
   target project.
3. Decide whether MyLoc should have a remote/upstream and be included in the
   standard aggregate verification surface.

## Optional Improvements

1. Add one-command pack installer with dry-run, overwrite protection, and
   post-install instructions.
2. Add cross-repo contract/runtime conformance tests.
3. Add a generated host-pack verification matrix document with current status:
   documented, discovery-verified, smoke-verified, or blocked by credentials.
4. Add CI or a local `make verify-agent-packs` wrapper that runs JSON,
   generator, unit, shell syntax, secret scan, and stale-reference checks.
5. Promote MyLoc and MoriahCareFrame into one maintained proof-index page with
   remote URLs, current heads, smoke commands, and last verification date.
