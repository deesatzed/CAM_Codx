# Decisions

## 2026-06-21: Keep Hub-And-Spoke Repo Ownership

Decision: keep CAM_Codx, CAM_CAM, generated products, and adapter surfaces as
separate repos/docs surfaces rather than merging them into one monorepo.

Reason: CAM_CAM owns runtime code and local databases; CAM_Codx owns Codex
workflow docs and goal templates; generated products need standalone repo
history and verification. This keeps public onboarding cleaner and limits the
risk of publishing local runtime state.

## 2026-06-21: Use Placeholders For CAM_ALL Local State First

Decision: create `/Volumes/WS4TB/CAM_ALL/local_state` with documented
placeholders instead of copying `CAM_CAM/data/claw.db` in this batch.

Reason: `claw.db` is local runtime state. The goal allows documented
placeholders, and avoiding a second copy reduces risk of stale databases or
accidental publication.

## 2026-06-21: Remove Only Classified Public Artifacts

Decision: remove tracked public files only after listing them in
`docs/repo_inventory/PUBLIC_REPO_CLEANUP_MANIFEST.json` and the local archive
manifest. Retain legacy-looking plans and design records when their current
replacement is not obvious.

Reason: the final cleanup goal requires a cleaner public GitHub state, but the
repo family has useful historical design material. Generated batch outputs,
stale launch reports, and old coverage snapshots are low-risk public removals;
broader plan/history deletion would risk losing context without improving
clone-and-run behavior.

## 2026-06-23: Keep CAM_Codx As Hub For Generated Agent Packs

Decision: build the Claude Code, Gemini, and Grok Build analogs as generated
agent packs inside CAM_Codx, backed by one shared CAM capability contract and
the existing CAM_CAM runtime/MCP core.

Reason: separate CAM_Claude, CAM_Gemini, or CAM_Grok repos would duplicate
policy, tool mappings, install examples, and verification rules. A shared
contract plus generated host packs gives each agent its native instructions and
MCP configuration while keeping maintenance anchored in CAM_Codx and runtime
truth anchored in CAM_CAM.

Constraint: CAM_Codx may own docs, templates, generator scripts, tests, and
pack artifacts. CAM_CAM continues to own executable runtime/MCP behavior unless
future verification proves a narrow runtime change is required.

## 2026-06-23: Generate Agent Packs From One Contract

Decision: make `agent-packs/contract/cam_agent_capabilities.json` the source of
truth for host pack capability lists, safety policy, runtime ownership, and
checked external doc references. `tools/generate_agent_packs.py` renders the
pack docs and checks them for drift.

Reason: hand-maintained Claude, Gemini, and Grok docs would drift as CAM_CAM
adds or changes MCP/CLI capabilities. A deterministic generator makes drift a
test failure while still leaving the generated files readable for users.

Constraint: generated pack examples may contain placeholders and environment
variable names, but they must not contain real API keys, auth data, local
databases, or machine-private runtime files.
