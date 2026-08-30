# Decisions

## 2026-08-30: Seal boundary grammar and brief display semantics

Decision: explicit boundary incompatibility is recognized on either side of an
exact per-need overlap. The bounded grammar covers `unsupported`,
`inapplicable`, `unrelated`, `cannot`/`can't`, `never applies`, `outside the
scope`, `excludes`/`excluded`, and `does not apply`. Read-only safety language
such as `without modifying`, `without writing`, `no mutation`, and `no write`
remains non-conflicting. A mixed candidate is still rejected only when every
relevant matched need conflicts.

Renderer safety analysis uses Unicode NFKC plus case-folding while preserving
the original safe prose for display. Code withholding requires structural
signals: braces, assignment, calls, declarations, shell/SQL forms, or numbered
imperative sequences. A semicolon or parenthetical alone is ordinary prose.
Numbered procedures are evaluated across the complete selected record, so two
or more ordered steps distributed between fields cannot evade per-field checks;
every participating prose field is replaced by the same neutral withholding
label. One ordinary numbered reference remains displayable.

Reason: phrase direction and compatibility characters must not change a
source boundary or safety decision, but conservative rendering also must not
erase harmless source prose. Evidence-item omission summaries reserve space
inside the fixed `64 KiB` aggregate instead of extending its bound. The exact
ranking formula and frozen `0.48` threshold remain unchanged.

## 2026-08-30: Scope boundary exclusions per need and withhold executable prose

Decision: a candidate boundary is evaluated independently for every recorded
need match. Explicit incompatibility forms such as `unrelated`, `inapplicable`,
`does not apply`, `unsupported for`, or direct `not <need term>` exclude that
need. Generic non-mutation boundaries such as `without modifying`, `does not
write`, and `no mutation` do not. Ranking chooses the strongest relevant,
non-conflicting matched need and rejects the candidate as `boundary_conflict`
only when every relevant match conflicts. Need audits retain every acquisition
match but attribute a selected record only to its chosen ranking need.

Additivity now credits a novel discriminative mechanism term only when that
same normalized term independently occurs in the exact need problem/query/span
or the source problem/context. Adjacent filler receives no credit. Equivalent
mechanism groups use deterministic complete-link containment: each new member
must be equivalent to every existing group member, preventing a broad bridge
record from joining two disjoint mechanisms.

Reason: source limitations apply to specific target needs, while read-only
safety statements are desirable constraints rather than incompatibilities.
Independent term support is inspectable and cannot be manufactured by
alternating filler. Complete-link grouping preserves padding resistance without
transitive over-grouping.

Safety: every dynamic record field is passed through one language-neutral,
fail-closed renderer filter. Assignments, braces, structurally code-shaped
semicolon forms, function calls, arrows, shell/SQL shapes,
C/Rust/Go/Swift-like constructs, and numbered multi-step instructions are
replaced with an explicit neutral withholding label. Evidence files and
symbols are sanitized item by item; their display is bounded to `64 KiB` per
aggregate with a deterministic omitted-item summary.
All valid Task 5 item sizes remain accepted, and the fixed score formula and
`0.48` threshold remain unchanged.

## 2026-08-30: Bind opportunity ranking and rendering to admitted evidence

Decision: ranking accepts only the exact, recursively revalidated Task 5
`AcquisitionReceipt` and exact `NeedTheme` sequence whose IDs and queries equal
the receipt calls. A candidate is scored only against the needs named by its
`CandidateMatch` values; there is no cross-need RRF fallback. A boundary
negation within a conservative local token window of an exact need overlap is
a hard `boundary_conflict` rejection.

Mechanism additivity admits only novel discriminative terms anchored to the
exact need or source problem/context. Handoff redundancy uses maximum token
containment over bounded individual handoff lines/sentences, and equivalent
mechanisms use containment grouping, so appended unrelated words cannot dilute
either decision. The exact score coefficients and frozen `0.48` threshold do
not change.

Reason: retrieval rank is evidence only for the query that produced it;
unmatched needs, contradictory source boundaries, repeated handoff material,
and arbitrary padding cannot support a target-facing selection. Frozen public
ranking children carry canonical integrity digests, the aggregate result
recomputes complete mechanism/source/need relations, and every selected record
must appear in a selected need audit. `dataclasses.replace` therefore cannot
silently detach a record, component, inference, or audit from its receipt.

Safety: rendering recursively revalidates the snapshot and ranking, encodes
every dynamic scalar for CommonMark, neutralizes ambiguous status language and
code-shaped source material, and applies a final unsafe-output gate. Negative
evidence is labeled `Negative lesson` with a distinct inference label rather
than being described as a mechanism that may help. These are inspection
dispositions, not target outcomes or implementation claims.

## 2026-08-30: Freeze opportunity ranking as inspectable ordering only

Decision: cross-repository opportunity inspection uses the exact decomposed
score `0.35 normalized_rrf + 0.25 need_relevance + 0.20
additive_beyond_handoff + 0.15 evidence_quality + 0.05
cross_context_transfer - 0.20 generic_match_penalty - 0.25
redundancy_penalty`. Every component is bounded to `[0, 1]` and retained in a
frozen disposition receipt. The minimum selection score is frozen at `0.48`,
with zero to five records selected after prioritizing source diversity and
deduplicating normalized mechanism identities.

Reason: `0.48` was fixed before the production implementation went GREEN. In
the public evidence-preservation fixture it admits the source-grounded Imbora
replay mechanism while Buzz, GenericAgent, an unrelated shader need, and a
handoff-equivalent mechanism abstain. A later threshold change requires an
explicit fixture amendment and a new decision; it cannot be hidden tuning.

Safety: this number orders bounded human inspection candidates. It does not
establish target usefulness, implementation status, scientific validity, or a
verified outcome. Rendered target mappings are explicitly labeled
`Inference`, preserve source evidence identity and boundaries, and omit
granular implementation steps.

## 2026-08-24: Decompose task obligations locally before corpus acquisition

Decision: CAM_Codx converts bounded public task text into frozen obligations
for invariants, failure, recovery, safety, order, persistence, verification,
current API needs, and unresolved spans. Each obligation retains the exact
source substring and offsets, stable content-derived identity, bounded generic
terms, and whether the source text explicitly made it optional. Serialization
is canonical schema-versioned JSON.

Reason: later CAM acquisition must query independently supported method needs
without importing donor identities, benchmark case labels, or hidden-test
knowledge. Generic syntactic cues provide a deterministic local starting point;
they do not claim semantic completeness. A span without a supported cue remains
`unresolved` instead of being guessed.

Safety: decomposition is pure and local. It performs no provider or Context7
call, corpus query, mining, database access, target mutation, or evidence
creation. Current-API classification requires an explicit currency cue or a
concrete version, so an internal API name or supplied runtime-version field
does not independently recommend external documentation. Top-level `and`
clauses are separated when a sentence contains a supported method cue, keeping
an unknown sibling clause explicitly unresolved. Bare domain nouns such as
`state` do not establish persistence, attributed source-method grammar fails
closed without a donor-name table, and serialization accepts only the exact
canonical decomposition of its preserved task text. Serialization validates
the exact resolution, obligation, enum, scalar, and tuple item types before
comparing values; Python equality between `True`/`1`, `0`/`0.0`, or a string
enum/plain string cannot cross this boundary. The top-level lexer treats
semicolon and adversative `but` as clause boundaries, while an `and` split
requires an independently clause-shaped right side so noun coordination stays
intact. Source attribution tokenizes the complete bounded task once around a
closed method-artifact grammar. Possessive artifact lookup is independent of
modifier count or leading action verb; only owner capture remains a bounded
local window. Rather than enumerate quote/Markdown wrappers, attribution token
edges strip any Unicode punctuation or symbol category in one bounded linear
pass while preserving internal apostrophes. Case and orthography cannot make an
attributed entity local: a named attribution is admitted only when a nonempty
exact normalized identity was declared earlier through bounded generic
declaration/construction syntax. Plain and backtick-delimited identifiers share
the same identity; one polite prefix, one closed method-action prefix, and one
optional article are syntax, not identity, and no other identity word is
discarded. Closed local-role and task-document grammar preserves ordinary
caller/task phrasing without creating an arbitrary lowercase bypass; the role
exemption compares the entire command-stripped owner phrase, never a suffix.
Terminal ASCII and curly plural possessives are recognized before Unicode edge
wrappers are stripped, including punctuation or symbol wrappers after the
apostrophe. They receive no special source exemption: only an exact earlier
declaration of the complete normalized owner identity is local.

Leakage seals apply NFKC and case folding, with camel separation only for the
hidden/held-out vocabulary seal. Case IDs use a linear identifier-boundary scan
and reject any number of non-alphanumeric separators before either of their two
digits. Repository candidates undergo bounded percent decoding and special-URL
backslash normalization before conservative authority parsing. Repository token
edges use the same Unicode punctuation/symbol stripping rule, so normalized
HTTP(S), SSH, Git, and scp-style identities cannot hide behind userinfo, ports,
hostname case, trailing dots, guillemets, emphasis, slash, pipe, or symbol
wrappers. Before those parsers run, bounded inspection scans both the original
scalar order and its NFKC view. Every Unicode general category `C` scalar is
rejected except tab, line feed, and carriage return; a frozen closed table also
covers default-ignorable non-`C` code points. A residual combining mark at a
token or punctuation/symbol/control structural edge is ambiguous and fails
closed before normalization can compose it away. Safely composed Unicode
identifiers and prose remain valid. Leakage matching additionally uses an NFKD
security skeleton with combining marks removed, so canonically decorated
possessive syntax cannot evade attribution. Declaration matching uses that
same skeleton, but decomposition and canonical serialization preserve the
original task and offsets exactly.
Persistence uses a closed conservative direct object grammar: a
persistence action must directly govern an allowlisted generic
state/artifact/storage head after only a bounded article and safe-modifier
prefix. An unknown word or secondary phrase before the head stays unresolved;
valid but unlisted terminology is intentionally not promoted. A recognized
head may precede a trailing phrase. Before action scanning, balanced code and
quotation spans are masked without changing offsets. Bounded passive forms and
an explicit object-survival relation across a restart-like event remain valid
only when the grammatical subject is itself a bounded state or artifact term.
Benefit/resource senses, decorative durability language, quoted persistence
words, standalone past-participle labels, and content following the closed
singular/plural textual directive set `quote`, `label`, `caption`, `title`,
`example`, `sample`, `note`, `text`, and `legend` plus a colon do not create a
persistence obligation. Incidental state-file, checkpoint, journal, backup, or
storage nouns likewise remain insufficient. A separate subsequent sentence is
still scanned normally.

Clause splitting classifies `and` by position: generic
action/modal/subject-predicate evidence starts a sibling clause, an explicit
known obligation predicate takes precedence over preceding prepositional
context, and a completed direct persistence object makes an otherwise unseen
base-form command fail closed into its own unresolved span. Coordination inside
a prepositional modifier or incomplete noun phrase remains intact, including
verb-like modifiers sharing a later plural head. Balanced backticks, supported
paired quotation marks (including canonical fullwidth ASCII forms), and
properly matched `()[]{}` nesting are required before decomposition; ambiguous
apostrophes, two-digit numeric elision apostrophes, and unit marks are not
promoted to quote delimiters. Other unmatched supported quotes continue to
fail closed. Invalid UTF-8 scalar content fails as
`TaskDecompositionError`. Code, quotations, nesting, exact offsets, and all
byte/token/window/span/obligation bounds remain preserved.

## 2026-08-23: Bound fallback recall before normal packet presentation

Decision: when CAM_CAM reports `any_terms_fallback`, CAM_Codx presents only the
strongest ranked result. Exact all-terms results retain the existing bounded
result behavior. Unknown query strategies fail closed, and a requested source
filename such as `solution.py` supplies the corresponding language hint.

Reason: the relaxed CAM query restored the correct held-out method to rank one
in five of five public tasks, but passing all fallback rows through would place
generic distractors into every packet. Normal CAM_Codx selection must improve
recall without silently degrading packet precision.

Safety: selection remains primary-only and read-only. It does not mine, call a
provider, mutate a target or corpus, or claim that the selected method produced
better software.

## 2026-08-23: Present source limitations separately from adaptations

Decision: parse and render CAM_CAM's bounded `source_limitations` and
`adaptation_requirements` fields as visibly separate method-contract sections.

Reason: the C29 source does not implement deterministic sorting. The sort is a
valid target hardening requirement, but presenting it as an extracted source
predicate would fabricate provenance.

Safety: unknown fields remain excluded, legacy payloads remain compatible, and
the brief continues to require target verification before positive trust.

## 2026-08-22: Show exact decision predicates in normal CAM_Codx evidence

Decision: add CAM_CAM's bounded `decision_predicates` field to the immutable
Development Brief `MethodContract` and render it explicitly beside the other
method semantics.

Reason: a predicate that controls branch behavior is actionable evidence, not
merely a retrieval keyword. Reducing it to "variable is set" can erase the
distinction between truthiness and key presence and between absent and empty
values.

Safety: CAM_Codx applies the existing 20-item/500-character bound and accepts
only the named field. Presentation remains read-only and does not imply correct
extraction, selection, builder use, safety, or software improvement.

## 2026-08-22: Present typed CAM method contracts in the Development Brief

Decision: the normal CAM_Codx Development Brief parses and renders CAM_CAM's
bounded `method_contract` and source provenance for direct precedents and
transferable analogies. It accepts only named fields and silently excludes
unknown payload keys.

Reason: the CAM-versus-Context7 outcome RCA established two diagnostic cases
where a selected CAM card lost method mechanics before reaching the builder.
CAM_Codx must preserve the runtime's structured semantics rather than reducing
them back to title and summary text.

Safety: the route remains read-only and primary-corpus-only. Rendering a
contract does not mine, call a provider, mutate a target/corpus/config/profile,
or confer positive outcome trust. The brief continues to label analogies and
hypotheses separately and requires target verification.

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
