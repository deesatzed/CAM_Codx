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
