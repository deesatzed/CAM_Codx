# MCP-Cortex Codex-CAM Showpiece Log

Date: 2026-05-22

Status: green. Native recall, provenance, outcome recording, and post-outcome verification completed.

Stop marker: cleared. Prior `MCP_NATIVE_TOOL_UNAVAILABLE` transport failure was resolved by the native `cam_cam` MCP surface in the final run.

## Goal

Run the GOAL.md showpiece using `/Volumes/WS4TB/_MyGhRepos/mcp-cortex-handoff` as the source methodology corpus, then apply one small MCP-Cortex-inspired Codex-CAM MCP improvement only after native `cam_cam` recall and provenance prove newly mined rows.

## Starting State

Codex-CAM implementation repo:

```text
## feature/initial-impl...origin/feature/initial-impl
?? 2026-05-20-104442-command-messagebrainstormingcommand-message.txt
?? GOAL.md
```

`GOAL.md` was the intentional saved run contract created before launching the independent Codex showpiece agent. The large transcript file was pre-existing and unrelated.

CAM_CAM repo:

```text
## main...origin/main
 M .env.example
```

Source folder git state:

```text
NO_GIT
```

Source folder top-level files:

```text
/Volumes/WS4TB/_MyGhRepos/mcp-cortex-handoff/.DS_Store
/Volumes/WS4TB/_MyGhRepos/mcp-cortex-handoff/CODEX_HANDOFF.md
/Volumes/WS4TB/_MyGhRepos/mcp-cortex-handoff/LICENSE
/Volumes/WS4TB/_MyGhRepos/mcp-cortex-handoff/README.md
/Volumes/WS4TB/_MyGhRepos/mcp-cortex-handoff/TEST_RESULTS.md
/Volumes/WS4TB/_MyGhRepos/mcp-cortex-handoff/docs
/Volumes/WS4TB/_MyGhRepos/mcp-cortex-handoff/examples
/Volumes/WS4TB/_MyGhRepos/mcp-cortex-handoff/package_manifest.json
/Volumes/WS4TB/_MyGhRepos/mcp-cortex-handoff/pyproject.toml
/Volumes/WS4TB/_MyGhRepos/mcp-cortex-handoff/pytest.ini
/Volumes/WS4TB/_MyGhRepos/mcp-cortex-handoff/schemas
/Volumes/WS4TB/_MyGhRepos/mcp-cortex-handoff/scripts
/Volumes/WS4TB/_MyGhRepos/mcp-cortex-handoff/src
/Volumes/WS4TB/_MyGhRepos/mcp-cortex-handoff/tests
```

## False Starts And Troubleshooting

1. Initial top-level source listing command had a local `sed` syntax error:

```text
sed: 1: "s#^#/##
": bad flag in substitute command: '#'
```

Fix: re-ran the listing with plain `find ... -print | sort`.

2. Exact full mining command failed during live API validation:

```text
cam mine-self --path /Volumes/WS4TB/_MyGhRepos/mcp-cortex-handoff
```

Result:

```text
OpenRouter failed: Request failed after 3 attempts: [Errno 8] nodename nor servname provided, or not known
```

3. Troubleshooting attempt used CAM_CAM's documented validation bypass to determine whether only the validation check was blocked:

```text
cam mine-self --path /Volumes/WS4TB/_MyGhRepos/mcp-cortex-handoff --no-live-keycheck
```

Result: validation was bypassed, but the actual LLM mining calls still failed with the same DNS/network error across model escalation, content reduction, and chunk mining. CAM_CAM ended with:

```text
Mining failed: All recovery strategies exhausted -- 0 findings
```

## Mining Evidence

Quick mining succeeded:

```text
cam mine-self --path /Volumes/WS4TB/_MyGhRepos/mcp-cortex-handoff --quick
```

Evidence summary:

```text
Project: mcp-cortex-handoff
Source files: 40
Total size: 79 KB
Scan signature: 70a70e9ee663...
Primary language: python
Complexity: small (40 files)
Primary domain: ai_integration
Secondary domains: testing, design_patterns, cli_ux
```

Full mining did not create findings because network DNS resolution was unavailable for the configured OpenRouter-backed model calls.

## Native MCP Recall Evidence

Native `mcp__cam_cam__.cam_recall` was available and accepted the required shape:

```json
{
  "query": "mcp-cortex handoff policy trace intent capability deterministic MCP compatibility",
  "k": 10,
  "include_embryonic": true
}
```

Result: `corpus_status` was `connected`, but returned rows were older MCP-related methodologies from other sources such as `hermes-vault`, `xmcp`, `velxio`, and `sendblue-mcp`. No returned row was newly mined from `mcp-cortex-handoff`.

Because native recall could not return newly mined `mcp-cortex-handoff` methodologies, the run stopped before provenance calls, code edits, tests, and outcome recording.

## Actions Not Taken

- No direct SQLite queries were used for showpiece proof.
- No copied databases were used.
- No JSON-RPC or Python subprocess CAM queries were used for recall, provenance, or outcome proof.
- No fabricated corpus rows were created.
- No MCP code was edited.
- No fifth MCP tool was added.
- No outcome was recorded because no methodology was applied.
- Commit and push were attempted by the independent Codex run only for this showpiece log, but staging was blocked by sandbox permissions because this worktree's Git index lives under `/Volumes/WS4TB/WS4TBr/CAM_Codx/codex-cam-methodology/.git/worktrees/codex-cam-methodology-impl/`, outside that run's writable roots.

## Remaining Risks

- Full mining depends on network/DNS access to the configured LLM provider.
- The saved `GOAL.md` contract and this showpiece log need to be committed by the parent session.
- The pre-existing implementation repo transcript `2026-05-20-104442-command-messagebrainstormingcommand-message.txt` remains untracked and unrelated.
- The pre-existing CAM_CAM `.env.example` modification remains dirty and was not touched.
- Commit/push should be retried from an environment that can write the linked worktree Git index.

## Initial Full-Access Retry Evidence (Superseded)

Retry timestamp: 2026-05-22 11:32:30 EDT.

Retry environment:

- Sandbox: `danger-full-access`.
- Explicitly avoided `--dangerously-bypass-approvals-and-sandbox`.
- Native CAM proof path only after mining: `mcp__cam_cam__.cam_recall`.
- No direct SQLite, copied database, JSON-RPC, Python subprocess CAM query, or fabricated corpus row was used for recall proof.

Starting states were rechecked.

Codex-CAM implementation repo:

```text
## feature/initial-impl...origin/feature/initial-impl
?? 2026-05-20-104442-command-messagebrainstormingcommand-message.txt
```

CAM_CAM repo:

```text
## main...origin/main
 M .env.example
```

Source folder git state:

```text
NO_GIT
```

Source folder top-level files:

```text
/Volumes/WS4TB/_MyGhRepos/mcp-cortex-handoff/.DS_Store
/Volumes/WS4TB/_MyGhRepos/mcp-cortex-handoff/CODEX_HANDOFF.md
/Volumes/WS4TB/_MyGhRepos/mcp-cortex-handoff/LICENSE
/Volumes/WS4TB/_MyGhRepos/mcp-cortex-handoff/README.md
/Volumes/WS4TB/_MyGhRepos/mcp-cortex-handoff/TEST_RESULTS.md
/Volumes/WS4TB/_MyGhRepos/mcp-cortex-handoff/docs
/Volumes/WS4TB/_MyGhRepos/mcp-cortex-handoff/examples
/Volumes/WS4TB/_MyGhRepos/mcp-cortex-handoff/package_manifest.json
/Volumes/WS4TB/_MyGhRepos/mcp-cortex-handoff/pyproject.toml
/Volumes/WS4TB/_MyGhRepos/mcp-cortex-handoff/pytest.ini
/Volumes/WS4TB/_MyGhRepos/mcp-cortex-handoff/schemas
/Volumes/WS4TB/_MyGhRepos/mcp-cortex-handoff/scripts
/Volumes/WS4TB/_MyGhRepos/mcp-cortex-handoff/src
/Volumes/WS4TB/_MyGhRepos/mcp-cortex-handoff/tests
```

Quick mining command:

```text
cam mine-self --path /Volumes/WS4TB/_MyGhRepos/mcp-cortex-handoff --quick
```

Quick mining result:

```text
Project: mcp-cortex-handoff
Source files: 40
Total size: 79 KB
Scan signature: 70a70e9ee663...
Primary language: python
Complexity: small (40 files)
Primary domain: ai_integration
Secondary domains: testing, design_patterns, cli_ux
```

Full mining command:

```text
cam mine-self --path /Volumes/WS4TB/_MyGhRepos/mcp-cortex-handoff
```

Full mining succeeded past the prior DNS failure. Evidence:

```text
OpenRouter: ok, model=deepseek/deepseek-v4-flash reply=OK
Files analyzed: 38
Findings: 12
Tokens used: 28827
Time: 85.2s
Findings tagged as 'mcp-cortex-handoff-self'.
```

Saved methodology IDs reported by mining:

```text
626d461d-d1c8-4cd1-a645-667b2672b0f4  [Mined from mcp-cortex-handoff-self] Intent-first deterministic policy engine
f89145a4-373f-42fb-a138-60b965803df9  [Mined from mcp-cortex-handoff-self] Stable digest for tamper-evident append-only trace
42bc219b-0c58-4efb-ba29-306e6d64e644  [Mined from mcp-cortex-handoff-self] ContextCell with provenance, labels, trust level
92959601-18dd-4cff-98a8-05aae42ed1b8  [Mined from mcp-cortex-handoff-self] Conservative wrapper with default forbidden effects
0e6a7318-0e9b-4b18-9542-dc01fadb7edf  [Mined from mcp-cortex-handoff-self] Gateway pattern with mandatory policy check
46fb6f48-59d6-4803-b45d-b4c0064740c5  [Mined from mcp-cortex-handoff-self] Deterministic policy with strict unknown effects
e6286ec9-ee0b-490c-be2f-81a8acdd66a7  [Mined from mcp-cortex-handoff-self] Effect vocabulary with risk classes and assurance
ad6d3f26-7ca8-4b2e-9c75-28ef0b4bcc81  [Mined from mcp-cortex-handoff-self] Subcommand CLI with validation and policy check
3f0f4ce2-5489-40b7-8b34-1e1a0e0f2fed  [Mined from mcp-cortex-handoff-self] Schema validation as integration tests
dd14d3b0-9598-4519-ae25-076da0d224cd  [Mined from mcp-cortex-handoff-self] In-memory context fabric with query by labels
c2086007-97bb-4701-8f7b-2a08d0a97246  [Mined from mcp-cortex-handoff-self] Data flow rules for sensitive label propagation
2e365c7b-943f-43c7-8dea-555569d1e656  [Mined from mcp-cortex-handoff-self] State handles with explicit URI scheme
```

Required native MCP recall command shape:

```json
{
  "query": "mcp-cortex handoff policy trace intent capability deterministic MCP compatibility",
  "k": 10,
  "include_embryonic": true
}
```

Native recall result:

```text
corpus_status: connected
corpus_size: 1144
degraded: false
returned rows: hermes-vault, xmcp, velxio, sendblue-mcp
new mcp-cortex-handoff-self rows returned: 0
```

Second native recall attempt used the fresh mining tag and title terms to distinguish a query-ranking miss from MCP visibility:

```json
{
  "query": "mcp-cortex-handoff-self Intent-first deterministic policy engine stable digest ContextCell provenance capability_data",
  "k": 12,
  "include_embryonic": true
}
```

Second native recall result:

```text
corpus_status: connected
corpus_size: 1144
degraded: false
returned rows: CAM-Pulse, ClawSwarm, aWSappFileSearch, deterministic_knowledge_retrieval, vllm-mlx, hermes-vault, claude-code-best-practice, ClinSafer, OpenViking, JRE-BSG-DHSW
new mcp-cortex-handoff-self rows returned: 0
```

Interim stop decision:

```text
MCP_NATIVE_TOOL_UNAVAILABLE
```

The full mining step produced 12 findings, but it ran from the implementation repo cwd and created a run-local untracked `data/` directory there. Native `cam_recall` could not return those rows because they were not mined into the CAM infrastructure repo backing the native MCP tool.

Mitigation: the generated implementation-repo `data/` directory was removed before rerunning mining from `/Volumes/WS4TB/WS4TBr/CAM_Codx/CAM_CAM`. This did not touch the pre-existing unrelated transcript file or CAM_CAM `.env.example`.

## CAM_CAM-Backed Retry Evidence

Retry timestamp: 2026-05-22 11:41:53 EDT.

Mining was rerun from the CAM infrastructure repo:

```text
cwd=/Volumes/WS4TB/WS4TBr/CAM_Codx/CAM_CAM
cam mine-self --path /Volumes/WS4TB/_MyGhRepos/mcp-cortex-handoff --quick
cam mine-self --path /Volumes/WS4TB/_MyGhRepos/mcp-cortex-handoff
```

Full mining result:

```text
OpenRouter: ok, model=deepseek/deepseek-v4-flash reply=OK
Files analyzed: 38
Findings: 10
Tokens used: 26629
Time: 143.2s
Findings tagged as 'mcp-cortex-handoff-self'.
```

Saved methodology IDs reported by the CAM_CAM-backed mining run:

```text
23b71c68-9073-40b6-9fce-9bfdeddfd2c2  [Mined from mcp-cortex-handoff-self] Deterministic Policy Engine with Effect Vocabulary
2d863aeb-e7a3-4c1d-bafb-b94033c60aa9  [Mined from mcp-cortex-handoff-self] Append-Only Trace Log with Content Digests
8975bf5c-3c0f-473f-aae7-27d17b3485ed  [Mined from mcp-cortex-handoff-self] ContextFabric In-Memory Store with Label Subset
5db663dd-313f-42a8-b531-9da2ce542df2  [Mined from mcp-cortex-handoff-self] Conservative Wrapper Pattern for External Tool Integration
96562f93-3510-442c-a963-00a5ce72537d  [Mined from mcp-cortex-handoff-self] Structured CLI with Subcommands and JSON Deserialization
531314ea-3a47-4f1f-863f-9da9ec30c0ee  [Mined from mcp-cortex-handoff-self] Automated Schema Validation of Example Files
79baef1a-1e36-42d1-94f7-a800ae8bc86e  [Mined from mcp-cortex-handoff-self] Frozen Dataclasses with Factory Classmethods
00c0d0e4-740d-4739-a582-3f510b63eb8e  [Mined from mcp-cortex-handoff-self] Human Action Card Template for Risk Communication
9c276358-35b1-470b-9004-0f5eb1b196be  [Mined from mcp-cortex-handoff-self] Incremental Adoption via Five-Stage Migration
95e0e1fa-60b3-405d-af61-abcf5e870b28  [Mined from mcp-cortex-handoff-self] CapabilityContract with Assurance Levels
```

Required native MCP recall command shape:

```json
{
  "query": "mcp-cortex handoff policy trace intent capability deterministic MCP compatibility",
  "k": 10,
  "include_embryonic": true
}
```

Native recall result:

```text
corpus_status: connected
corpus_size: 1154
degraded: false
returned rows: 10 newly mined mcp-cortex-handoff-self methodologies
```

Applied methodology:

```text
2d863aeb-e7a3-4c1d-bafb-b94033c60aa9
[Mined from mcp-cortex-handoff-self] Append-Only Trace Log with Content Digests
```

Native provenance result:

```text
found: true
source_path: src/mcp_cortex/trace.py
tags: mined, source:mcp-cortex-handoff-self, category:cross_cutting, brain:python
summary: deterministic SHA256 digest from sorted JSON serialization for tamper-evident trace events
```

Implementation:

```text
src/claw_codex_mcp/tools/record_outcome.py
tests/codex_mcp/test_record_outcome.py
```

The narrow update stores deterministic `codex-cam.invocation.v1` metadata inside `cam_record_outcome` evidence. The metadata includes the tool name, sorted methodology IDs, task ID, repo, outcome, run hash, and a canonical SHA-256 input digest. The public output schema remains unchanged, and the registered MCP tool count remains exactly four.

Verification:

```text
pytest tests/codex_mcp/test_record_outcome.py -q
8 passed in 0.08s

pytest tests/codex_mcp/ -q
68 passed in 2.30s

python tools/product_smoke.py
PRODUCT SMOKE PASS work_dir=/private/tmp/cam_codex_mcp_product_smoke

git diff --check
pass
```

Stable run hash prepared for native outcome recording:

```text
fc3f4aa128643c3fb6703a452c14f441063719fca1bfc5baef8bd5da8cdfdcc1
```

Native outcome recording attempts:

```text
mcp__cam_cam__.cam_record_outcome
result: failed
error: CamRecordOutcomeOutput rejected extra invocation_digest from an intermediate incompatible output-field attempt.
```

Mitigation:

- The code was tightened to keep invocation metadata inside stored evidence only and leave `CamRecordOutcomeOutput` unchanged.
- The focused and full verification gates were rerun successfully.
- The stale current-session `python -m claw_codex_mcp --transport stdio` helper process was terminated so the native tool could reload compatible code.

Final native tool state:

```text
mcp__cam_cam__.cam_record_outcome
result: failed
error: Transport closed

mcp__cam_cam__.cam_recall
result: failed
error: Transport closed
```

Stop decision:

```text
MCP_NATIVE_TOOL_UNAVAILABLE
```

The showpiece reached implementation and local verification, but did not complete native outcome recording, commit, or push because the required native `cam_cam` transport became unavailable. No direct SQLite, copied database, JSON-RPC, Python subprocess CAM query, or fabricated corpus row was used as a substitute for the native outcome proof.

## Final Native Completion Evidence

Final retry timestamp: 2026-05-22 15:46:13Z.

Required native recall was run through `mcp__cam_cam__.cam_recall` only:

```json
{
  "query": "mcp-cortex handoff policy trace intent capability deterministic MCP compatibility",
  "k": 10,
  "include_embryonic": true
}
```

Native recall result:

```text
corpus_status: connected
corpus_size: 1154
degraded: false
returned rows: 10 newly mined mcp-cortex-handoff-self methodologies
included methodology_id: 2d863aeb-e7a3-4c1d-bafb-b94033c60aa9
source_path for included row: src/mcp_cortex/trace.py
snippet: CLAW currently lacks an append-only, tamper-evident audit trail.
```

Native provenance was run through `mcp__cam_cam__.cam_provenance` only:

```json
{
  "methodology_id": "2d863aeb-e7a3-4c1d-bafb-b94033c60aa9"
}
```

Native provenance result:

```text
found: true
corpus_status: connected
methodology_id: 2d863aeb-e7a3-4c1d-bafb-b94033c60aa9
name: [Mined from mcp-cortex-handoff-self] Append-Only Trace Log with Content Digests
source_path: src/mcp_cortex/trace.py
tags: mined, source:mcp-cortex-handoff-self, category:cross_cutting, brain:python
summary: deterministic SHA256 digest from sorted JSON serialization for tamper-evident trace events
```

Native outcome recording was run through `mcp__cam_cam__.cam_record_outcome` only:

```json
{
  "methodology_ids": ["2d863aeb-e7a3-4c1d-bafb-b94033c60aa9"],
  "repo": "/Volumes/WS4TB/WS4TBr/CAM_Codx/codex-cam-methodology-impl",
  "task_id": "mcp-cortex-showpiece-invocation-trace",
  "outcome": "green",
  "run_hash": "fc3f4aa128643c3fb6703a452c14f441063719fca1bfc5baef8bd5da8cdfdcc1"
}
```

Native outcome result:

```text
recorded: true
outcome_id: b0dfe005-d8d6-4c05-8248-ff86fd854d93
duplicate: false
corpus_status: connected
ts: 2026-05-22T15:46:13Z
```

Post-outcome verification was rerun after native outcome success:

```text
pytest tests/codex_mcp/test_record_outcome.py -q
8 passed in 0.09s

pytest tests/codex_mcp/ -q
68 passed in 2.57s

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

git diff --check
pass
```

Final constraints check:

- Native `cam_cam` MCP tools were the only proof path for recall, provenance, and outcome recording.
- No direct SQLite query, copied database, JSON-RPC call, Python subprocess CAM query, or fabricated corpus row was used for the showpiece proof.
- The implementation preserved the four-tool MCP ceiling.
- The unrelated transcript file and CAM_CAM `.env.example` modification were not touched.
