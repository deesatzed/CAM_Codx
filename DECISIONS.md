# Decisions

## 2026-08-21: Route typed knowledge needs by least sufficient cost

Decision: CAM_Codx selects among `cam`, `context7`, `cam_context7`,
`raw_source`, and `abstain` using an exact typed signal contract. Local CAM
evidence is preferred when sufficient; current public API needs route to
Context7; mixed local/current needs combine them; stale evidence requiring
inspection routes to source; offline or unsatisfied combinations abstain.

Reason: route selection should not require the user to know a repository or
choose an MCP service. It also must not claim that one available source is
sufficient for a conjunction that needs both local and current evidence.

Constraint: the router never starts mining, external calls, or source reads.
Its relative cost units describe a plan, not billed spend. Evidence-state
calibration and final executable outcomes remain separate gates.

## 2026-08-21: Present typed managed outcomes without flattening evidence state

Decision: CAM_Codx derives later-recall recommendations only from active
`verified_success` managed outcomes with test references and verification
receipts. Historical verified failures remain warnings, and every
`new_hypothesis` candidate remains explicitly unverified regardless of its
selection state.

Reason: a source-to-outcome report already preserves the runtime truth in
CAM_CAM. CAM_Codx needs a normal-user presentation layer, not a second outcome
database or a prose heuristic that could promote a failed or hypothetical
record.

Constraint: a positive count mismatch, missing verification evidence, or
positive trust/recipe eligibility on a non-success outcome fails closed. The
current E6 proof uses CAM_CAM's real managed-run service in disposable memory;
it is fixture proof and does not mutate the canonical corpus.

## 2026-08-18: Keep MatrAIx/SESA as a separate product-boundary goal

Decision: complete the CAM_Codx/CAM_CAM documentation synchronization, then
govern the MatrAIx/SESA vertical slice with a discovery-first
`GOAL_TASK_14_MATRAIX_SESA.md`. Do not infer its target checkout, source
revisions, license rights, privacy rules, provider policy, or writable paths
from the component names or historical documents.

Reason: Tasks 1-13 prove the control plane and fixture source-to-outcome chain,
but they do not prove a real product slice. Mixing an unresolved target into
the completed control-plane goal would turn a missing product decision into an
implementation assumption.

Safety: read-only local discovery and contract editing may continue without
product approval. Provider calls, paid mining, live import, target mutation,
model/profile changes, deployment, and destructive actions remain separate
explicit approvals. Fixture evidence must remain labeled as fixture proof.

## 2026-08-18: Consolidate CAM roots without swapping runtime state

Decision: use `/Volumes/WS4TB/waswiki/CAM_Codx` and
`/Volumes/WS4TB/waswiki/CAM_CAM` as the single canonical code checkouts, and
keep the existing CAM_CAM `claw.db`, `claw.toml`, and mode-0600 `.env` as the
single runtime state set. Fast-forward code from the pushed recovery heads;
do not copy or replace state files.

Reason: the recovery worktrees contain the verified code but no second
database/secrets set. Fast-forwarding clean canonical checkouts preserves the
existing corpus and configuration while eliminating runtime ambiguity.

Constraint: the Downloads worktrees remain recoverable references. Any future
state migration requires a separate explicit plan and backup/rollback proof.

## 2026-08-18: Test Task 14 through read-only CAM_Codx proof first

Decision: exercise the MatrAIx/SESA concept through CAM_Codx `assess` and
`cam_control_plane.py plan` before creating a candidate ledger, landing code,
or running a provider/model. The first proof uses the canonical CAM runtime in
read-only mode and a stable SWE Run ID.

Reason: both source checkouts lack CAM-native truth artifacts and the primary
corpus returned no matching evidence. The safety/orchestration path can still
be proven, but useful mine-to-build evidence must not be invented from an empty
or weak result.

Safety: no source code, prompts, tests, datasets, model artifacts, database,
configuration, or environment secrets were copied or changed. SESA root-code
reuse remains unresolved; the next implementation, if authorized, must be an
independent clean-room adapter using temporary state.

## 2026-08-17: Route sparse graph context through one CAM_Codx packet

Decision: register CAM_CAM's hidden `knowledge-graph-query` as one canonical,
managed, read-only CAM_Codx operation under the knowledge route. The packet
uses fixed list-form argv and carries an existing database, immutable snapshot,
and canonical seed as caller-supplied bounded inputs. It requires no approval.

Reason: CAM_Codx should present graph context as an outcome—`Use CAM_Codx to
assess the impact of ...`—while direct CAM_CAM remains a troubleshooting
surface. A separate provider, graph database, or duplicated traversal in
CAM_Codx would split runtime truth.

Safety: the route cannot create snapshots, scan sources, call providers, load
models, mutate targets, or change configuration. The CAM_CAM query enforces
two-hop/size limits, receipt provenance, association exclusion, and stale
revision rejection.

## 2026-08-18: Keep the Task 12 stale-path correction in the active plan

Decision: update the active control-plane implementation plan to reference
`tests/test_application_packet.py`, the actual CAM_CAM checkout path. Retain
the old `tests/planning/...` spelling only in the continuation contract's
description of what was corrected.

Reason: a release gate is not durable if its source-of-truth plan still points
at a nonexistent test. The current full-suite receipt and focused commands now
agree with the checked-out repository.

Safety: this is a documentation-only correction. No runtime, database,
configuration, provider, model profile, or target repository was changed.

## 2026-08-15: Bind Pull/Mine Bounds Before Manager Execution

Decision: derive a manager `mine-workspace` packet from the existing pull/mine
coordinator's validated configuration rather than recreating mining arguments
in CAM_Codx. The packet must match the resolved CAM command, corpus, config,
and optional profile identities; carries source, exact model, repository/time/
cost caps, and the future budget-receipt path; and is prepared but not executed
by the control plane.

Reason: the coordinator already owns mining-specific safety semantics. Reusing
its argv builder makes the registry-selected packet approval-bound without
adding a provider client or a second mining implementation.

Constraint: packet preparation is not mining approval or execution. It does
not create a budget receipt, change the corpus, select a build, or dispatch a
candidate. Execution and receipt-to-managed-run linkage require a later bounded
phase with the corresponding explicit authorization.

## 2026-08-15: Bind Target-Code Mutation Approval To A Reviewed Managed Plan

Decision: every CAM_Codx manager packet whose registry policy is
`target_code_mutation` must name an existing target directory and carry a
non-empty reviewed managed-plan ID plus a lowercase 64-character plan SHA-256.
Both values are included in the packet scope digest that is bound to its
single-use approval.

Reason: phase approval must authorize one exact planned mutation, not grant a
portable mutation right across reviewed plans or target repositories.

Constraint: this binds manager authorization only; it does not execute a CAM
command, alter a target, or turn a plan into verification evidence. A later
verification receipt remains required before a positive outcome can be
recorded.

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

## 2026-07-06: Use A Setup-Generated CAM Wrapper For Codex Approval

Decision: CAM_Codx setup generates a narrow `cam-codx` wrapper under the local
CAM overlay instead of asking users to grant broad filesystem or shell access.

Reason: Codex sandboxes may be able to read a CAM_CAM install but not write
SQLite sidecars or evaluation records beside `claw.db`. A stable wrapper pins
the CAM_CAM checkout, `.env`, `claw.db`, and `claw.toml`, giving users one
specific command prefix to approve while keeping secrets out of logs and Git.

Constraint: the wrapper does not bypass user approval or authorize live CAM
mutation by itself. It only makes the requested approval bounded and repeatable.

## 2026-08-09: Require Reviewed Adoption After Mining

Decision: treat newly mined methodologies as evidence inputs, not permission to
modify CAM. CAM_Codx must produce a reviewed adoption manifest before provider
spend, active-file edits, or self-enhancement promotion can follow a mining run.

Reason: the latest run stored 80 useful but embryonic findings. CAM already has
staged self-enhancement, specialist exchange, PULSE, model tournament, and
rollback capabilities, so blindly adopting high-potential findings would
duplicate behavior and bypass outcome evidence.

Constraint: `cam self-enhance status` is a threshold signal only. Readiness must
eventually include corpus delta, evidence quality, observed outcomes, explicit
selection, verification, and rollback.

## 2026-08-09: Bind Active CAM Truth To repo622sn

Decision: use `/Volumes/WS4TB/repo622sn/CAM_CAM`, its tracked `claw.toml`, and
its root `claw.db` as the authoritative runtime/config/corpus tuple for current
CAM_Codx operations.

Reason: the default editable Python import still resolves an older WS4TBr
checkout unless `PYTHONPATH` is pinned. Active documentation and preflight must
make split-brain execution visible and fail closed before mutation or spend.

Constraint: old paths in historical plans and handoffs remain historical
evidence; current goals, contracts, setup guidance, and runtime checks must use
the authoritative tuple.

## 2026-08-10: Make CAM_Codx A Routine, Explicit SWE Manager

Decision: add a CAM_Codx packet/approval manager and installable `cam-codx-swe`
Codex skill for normal build, update, debugging, and review tasks.

Reason: CAM's experiential knowledge and evidence gates are useful during SWE
work, but the prior mining mistake showed that routine use must not imply
repository mining, provider spend, model promotion, or self-modification.

Constraint: the manager owns workflow policy and receipts only. CAM_CAM owns
runtime behavior. Mutating/spend phases require a matching, unexpired,
single-use approval; self-enhancement swap always needs a separate promotion
approval and rollback evidence.

## 2026-08-10: Keep Development Brief Recall Primary-Only By Default

Decision: make the Development Brief query only an explicitly supplied primary
CAM database through CAM_CAM's side-effect-free `brief-query` command. A named
local source expansion is planning-only until an operator reviews and approves
it.

Reason: normal recall paths can record retrieval usage, and stale sibling paths
after workspace relocation make a broader corpus search unreliable. A concise
SWE decision aid must not hide a database write, federation failure, or
repository scan behind a recall request.

Constraint: each additional source root must be explicitly named, exist below
an approved parent, and pass the relocation gate. A failed gate renders its
unavailable paths and prevents a wider search; it does not repair configuration
or invoke any scan/mining command.

## 2026-08-11: Bound Pull/Mine Invocation To One Controlled Evidence Cycle

Decision: invoking `cam-codx-pull-mine-dir` authorizes only its bounded cycle:
safe fast-forward updates for eligible repositories, scan and live
changed-only/no-task mining against one explicit corpus, normal corpus
ledger/receipt updates, evidence assessment, and at most one manager-backed
supervised candidate with `--max-tasks 1 --skip-swap` when the meaningfulness
threshold is met.

Reason: the workflow should make prior work useful during early development and
rescue work without turning ordinary invocation into open-ended provider spend
or mutation of the CAM runtime.

Constraint: the invocation never authorizes `self-enhance swap`, model or
profile promotion/rollback, live source edits, or live configuration changes.
Those remain separate explicit operations with their own manager approval and
rollback evidence. Repositories that are dirty, conflicted, detached, lack an
upstream, or cannot fast-forward are reported and skipped or failed without
blocking unrelated eligible repositories.

## 2026-08-11: Require an Explicit Semantic-Gap Attestation

Decision: derive the numeric evidence gate from the pinned corpus and mining
ledger, but require the operator to pass `--repeated-pattern-or-gap` before a
meaningful mining result may dispatch the supervised `--skip-swap` candidate.

Reason: the current corpus and ledger can truthfully establish methodology
deltas and source-repository provenance, but cannot by themselves prove the
semantic conclusion that a repeated pattern or concrete capability gap exists.
Defaulting that conclusion to false avoids an invented candidate trigger.

Constraint: the attestation authorizes only the one already-bounded candidate.
It does not grant a self-enhance swap, model/profile change, rollback, source
edit, or live configuration change.

## 2026-08-12: Make CAM_Codx The Normal Control Plane For CAM_CAM

Decision: CAM_Codx will manage every CAM_CAM feature through one semantic
user-facing skill. Direct CAM_CAM CLI use remains supported for runtime
troubleshooting, development, recovery, and regression isolation rather than
as the normal product workflow.

Reason: CAM_CAM already has broad and useful runtime capabilities, but its
expert command surface and CAM_Codx's overlapping skills require users to know
internal architecture. One control plane lets CAM_Codx choose the right route,
show side effects, enforce approvals, and carry evidence across phases.

Constraint: CAM_CAM retains runtime and database ownership. CAM_Codx may route,
approve, and explain runtime calls but must not vendor or reimplement them.

## 2026-08-12: Use One Canonical CAM_Codx Skill

Decision: converge the normal Codex UX on one `cam-codx` skill. The current
setup, SWE, Development Brief, pull/mine, session, model, and self-enhancement
instructions become internal playbooks and helpers.

Reason: the user should be able to ask CAM_Codx for an outcome without first
choosing among implementation-specific skills.

Constraint: implementation must preserve a recoverable migration for existing
installed skills and must not claim the one-skill UX is current until its tests
and setup migration pass.

## 2026-08-12: Reuse CAM-SEQ For The Mine-To-Build Evidence Chain

Decision: present one SWE Run that links mining receipts, candidate decisions,
application packets, landing events, verification, and outcomes through
CAM_CAM's existing CAM-SEQ tables and event stream.

Reason: CAM_CAM already contains the storage primitives needed to prove how
mined knowledge affected a build. A parallel CAM_Codx database or reuse schema
would duplicate truth and make attribution harder to audit.

Constraint: mining rows or retrieval similarity alone are not proof of useful
reuse. Candidate selection is explicit, and only verified outcomes may
strengthen trust evidence.

## 2026-08-12: Supersede The repo622sn Runtime Binding

Decision: active CAM_Codx operations now resolve CAM_Codx from
`/Volumes/WS4TB/waswiki/CAM_Codx`, CAM_CAM from
`/Volumes/WS4TB/waswiki/CAM_CAM`, and the default source pool from
`/Volumes/WS4TB/waswiki/repos2mine/repo622sn`.

Reason: the repositories were reorganized after the 2026-08-09 binding
decision. Continuing to advertise the former checkout as active creates a
split-brain risk.

Constraint: earlier paths remain historical evidence. Active docs, setup, and
preflight must use resolved current paths and fail closed on ambiguity.

## 2026-08-16: Model-comparison verdict is read-only evidence

Decision: register `models benchmark compare` as a managed, read-only CAM_CAM
route and expose it through the `benchmark-compare` CAM_Codx manager alias.
It accepts completed first-round, heldout, and repeat reports and emits a
non-promoting baseline verdict.

Reason: users need a clear answer about whether a candidate helped mining
before considering any profile change. Reusing the evidence-only CAM_CAM
comparison service avoids duplicating tournament or selection logic in
CAM_Codx.

Constraint: a `better` verdict never edits a model profile, selects a live
model, spends provider funds, or authorizes a benchmark run. Each of those
actions remains a separate scoped operation and approval.
