# CAM + CAM_Codx Operator Cheat Sheet

> **UX direction approved 2026-08-12:** CAM_Codx will become the single normal
> control plane for every CAM_CAM feature. Direct CAM_CAM commands in this
> document remain useful for troubleshooting and runtime development. The
> canonical one-skill implementation is planned, not yet complete; current
> commands and current four-skill setup remain documented truth below.

Normal future phrasing will be `Use CAM_Codx to <desired outcome>`. See
`CAM_CAPABILITY_AUDIT_2026-08-12.md` for the complete current inventory and
approved route map.

This is an operator reference for the current CAM family:

| Role | Location | Owns |
| --- | --- | --- |
| CAM_CAM | `/Volumes/WS4TB/waswiki/CAM_CAM` | Runtime, CLI, MCP, models, mining, local knowledge databases |
| CAM_Codx | `/Volumes/WS4TB/waswiki/CAM_Codx` | Codex workflows, approval manager, skills, setup, agent packs, evidence templates |
| Mining source pool | `/Volumes/WS4TB/waswiki/repos2mine/repo622sn` | Candidate repositories to inspect or mine |
| CAM Assistant | `/Volumes/WS4TB/waswiki/CAM_Assistant` | Separate end-user product; not the CAM mining/runtime engine |

CAM output is evidence, not permission to edit code, change a model, spend
provider money, or claim completion.

## 1. Safety legend

| Label | Meaning |
| --- | --- |
| Read-only | Does not intentionally change a repository, model profile, or CAM corpus. It can still read local data or contact a remote service when stated. |
| Local write | Writes a report, plan, task, database record, or generated artifact. |
| Provider/spend | Can call a configured model provider; freeze scope and maximum budget first. |
| Code mutation | Can change a target repository or CAM itself; requires a clean/documented tree, tests, diff review, and explicit approval. |
| High risk | Long-running, broad, external, or promotion/swap action; use a bounded pilot and rollback path. |

Always stop for: an ambiguous database target, missing credentials, protected or
sensitive data, an unclear dirty tree, unbounded spend, production deployment,
or a requested model/self-enhancement promotion.

## 2. One-time moved-checkout bootstrap

The current shell-safe runtime entrypoint is the moved source tree, not an
unqualified `cam` executable that might import another checkout.

```bash
export CAM_CAM=/Volumes/WS4TB/waswiki/CAM_CAM
export CAM_CODEX=/Volumes/WS4TB/waswiki/CAM_Codx
export CAM_DB="$CAM_CAM/claw.db"
export CAM_CONFIG="$CAM_CAM/claw.toml"

set -a
source "$CAM_CAM/.env"       # Loads names and values locally; never print them.
set +a

export CLAW_DB_PATH="$CAM_DB"
export CAM_CODEX_MCP_DB_PATH="$CAM_DB"

cam_local() {
  PYTHONPATH="$CAM_CAM/src" python -m claw.cli "$@"
}
```

Run these first:

```bash
cam_local status -c "$CAM_CONFIG"
cam_local stats --json -c "$CAM_CONFIG"
cam_local doctor status
cam_local models current
```

### Relocation gate

Before using `federate`, cross-ganglion `kb` queries, or polyglot mining,
update the four `instances/*/claw.db` paths in `CAM_CAM/claw.toml`. They still
refer to the pre-move `/Volumes/WS4TB/repo622sn/instances/...` location; the
current instances are under
`/Volumes/WS4TB/waswiki/repos2mine/repo622sn/instances/...`.

For a main-database-only integrity check that never creates WAL/SHM files:

```bash
sqlite3 "file:$CAM_DB?mode=ro&immutable=1" 'pragma integrity_check;'
```

`ok` checks the immutable main database image. It intentionally does not claim
that any uncheckpointed WAL data or unavailable federated database is valid.

## 3. Fast route: choose the right tool

| Desired outcome | Start here | Do not start with |
| --- | --- | --- |
| Start a new project or decide how to rescue one | `cam-codx-development-brief` | Mining, a provider call, or autonomous repair |
| Understand a repo safely | `evaluate --mode structural` or `preflight` | `enhance` |
| Reuse past CAM knowledge | `kb search`, `federate`, or MCP `query_memory` | Mining the target again |
| Assess a GitHub repo before cloning | `premine` | Clone/execute it |
| Learn from local repos | `mine --scan-only --changed-only` | A live mining run |
| Make an improvement plan | `camify --output ...` | Autonomous enhancement |
| Change one existing project | `enhance --dry-run`, then supervised `--max-tasks 1` | Fleet enhancement |
| Create a new project | `ideate`, then an evidence-gated Codex goal | `create --execute` |
| Prove CAM helped | `ab-test` with a frozen evaluator | Anecdotal output comparison |
| Compare mining models | `models benchmark fixtures/plan/.../select` | `models set` |
| Improve CAM itself | `self-enhance status`, then a supervised no-swap pilot | Direct `swap` |

## 4. CAM command index

Use `cam_local <command> --help` for every command's precise flags. Commands
below are grouped by outcome; the listed safety state is the default, not a
substitute for checking flags and scope.

### Setup, health, and orientation

| Command | What it does | Start command | Safety |
| --- | --- | --- | --- |
| `init` | Guided first-run CAM-PULSE setup | `cam_local init` | Local write / credentials |
| `setup` | Configure API keys, models, and agents | `cam_local setup` | Local write / credentials |
| `status` | Show CAM system status | `cam_local status -c "$CAM_CONFIG"` | Read-only |
| `stats` | Count methodologies, repos, ganglion, and CAG state | `cam_local stats --json -c "$CAM_CONFIG"` | Read-only |
| `doctor keycheck` | Check key availability by name | `cam_local doctor keycheck` | Read-only |
| `doctor expectations` | Check core runtime product expectations | `cam_local doctor expectations` | Read-only |
| `doctor audit` | Audit high-trust methodology evidence | `cam_local doctor audit` | Read-only |
| `doctor routing` | Show routing weights by task type | `cam_local doctor routing` | Read-only |
| `chat` | Interactive CAM workflow guide | `cam_local chat` | Interactive |
| `dashboard` | Open the federated knowledge explorer | `cam_local dashboard` | Read-only / opens UI |

### Inspect a repository and decide

| Command | What it does | Start command | Safety |
| --- | --- | --- | --- |
| `evaluate` | Measure enhancement potential | `cam_local evaluate /path/to/repo --mode structural -c "$CAM_CONFIG"` | Read-only in `structural`; `quick`/`full` can use providers and store results |
| `preflight` | Scope a specific requested change, requirements, and checks | `cam_local preflight /path/to/repo --request "..." --no-live -c "$CAM_CONFIG"` | Read-only by default |
| `premine` | Remote GitHub triage before clone/mining | `cam_local premine owner/repo --format markdown --report /tmp/premine.md` | Read-only remote |
| `security status` | Check secret-scanner availability | `cam_local security status` | Read-only |
| `security scan` | Scan a directory for hardcoded secrets | `cam_local security scan /path/to/repo --json` | Read-only scan |

### Learn from repositories and manage knowledge

| Command | What it does | Start command | Safety |
| --- | --- | --- | --- |
| `mine` | Mine direct-child local repositories into CAM knowledge | `cam_local mine /path/to/repos --scan-only --changed-only --no-tasks -c "$CAM_CONFIG"` | Scan-only is read-only; live mining writes `claw.db` and can spend |
| `mine-workspace` | Mine repositories across multiple roots | `cam_local mine-workspace --help` | Local write / provider spend when live |
| `mine-all` | Bulk pipeline: scan, preview, schema, mine, report | `cam_local mine-all --help` | Local write / provider spend when live |
| `mine-self` | Extract reusable patterns from the current project | `cam_local mine-self --quick --no-tasks -c "$CAM_CONFIG"` | Verify the build first; live mode writes knowledge |
| `enrich` | Assimilate embryonic findings more deeply | `cam_local enrich --help` | Local write / provider spend |
| `gaps` | Show knowledge coverage gaps | `cam_local gaps -c "$CAM_CONFIG"` | Read-only |
| `kb insights` | Show top capabilities, domains, and synergies | `cam_local kb insights` | Read-only |
| `kb search` | Search capabilities across CAM brains | `cam_local kb search "error handling"` | Read-only; federation gate applies |
| `kb capability` | Deep dive on one capability | `cam_local kb capability <name>` | Read-only |
| `kb patterns` | Show promoted methodologies with evidence | `cam_local kb patterns` | Read-only |
| `kb domains` / `kb synergies` / `kb brains` | Explore knowledge landscape and brain distribution | `cam_local kb domains` | Read-only |
| `kb seed` / `kb bootstrap` | Load starter knowledge | `cam_local kb bootstrap` | Local database write |
| `kb export-kit` | Export selected knowledge as a pack | `cam_local kb export-kit --help` | Artifact write |
| `kb community` | Share/import knowledge through community mechanisms | `cam_local kb community --help` | External/local mutation |
| `kb instances` | Manage ganglia, manifests, cross-ganglion queries | `cam_local kb instances --help` | Configuration and local writes possible |
| `federate QUERY` | Synthesize matches across every configured ganglion | `cam_local federate "testing strategy" --json -c "$CAM_CONFIG"` | Read-only after relocation gate |
| `cag status` | Inspect Cache-Augmented Generation state | `cam_local cag status --help` | Read-only |
| `cag rebuild` | Rebuild a ganglion's CAG cache | `cam_local cag rebuild --help` | Local write / potentially expensive |
| `cag convert` | Convert an external RAG source into CAG | `cam_local cag convert --help` | Local write / external-input risk |
| `learn search` | Semantic methodology search | `cam_local learn search "..."` | Read-only |
| `learn report` / `delta` / `reassess` / `synergies` | Learning lifecycle reports and analyses | `cam_local learn report --help` | Mostly read-only; inspect help |
| `learn usage` / `proof` | Show retrieval attribution and retrieved-to-success funnel | `cam_local learn proof` | Read-only |
| `learn backfill-components` / `ingest-codex-outcomes` | Build component cards or persist outcome records | `cam_local learn ingest-codex-outcomes --help` | Local database write |

### Plan and improve a project

| Command | What it does | Start command | Safety |
| --- | --- | --- | --- |
| `camify` | Analyze a repo against CAM knowledge and write an enhancement plan | `cam_local camify /path/to/repo --goal "improve tests" --output /path/to/repo/CAM_PLAN.md -c "$CAM_CONFIG"` | Plan-file write |
| `enhance` | Evaluate, plan, dispatch, verify, and learn | `cam_local enhance /path/to/repo --dry-run --mode supervised --max-tasks 1 -c "$CAM_CONFIG"` | Code/task/database mutation without `--dry-run` |
| `fleet-enhance` | Enhance many repositories | `cam_local fleet-enhance --help` | High-risk broad code mutation |
| `task add` | Add a CAM task/goal | `cam_local task add --help` | Local write |
| `task quickstart` | Prepare an operator quickstart | `cam_local task quickstart --help` | Artifact write |
| `task runbook` | Produce a runbook | `cam_local task runbook --help` | Artifact write |
| `task results` | Inspect task outcomes | `cam_local task results --help` | Read-only |

### Create and validate new work

| Command | What it does | Start command | Safety |
| --- | --- | --- | --- |
| `ideate` | Generate 1–8 new product concepts from knowledge and candidate repos | `cam_local ideate /path/to/candidates --focus "local developer tools" --ideas 3` | Planning; can call configured agent |
| `create` | Create a fixed, augmented, or new repository from an outcome | `cam_local create --help` | Code/artifact mutation; freeze output path and acceptance checks |
| `validate` | Validate a created repo against its saved creation spec | `cam_local validate --spec-file /path/to/spec.json` | Read-only validation |
| `forge export` | Export knowledge packs | `cam_local forge export --help` | Artifact write |
| `forge benchmark` / `benchmark` | Benchmark Forge output | `cam_local forge benchmark --help` | Writes reports; may be costly depending on inputs |
| `ab-test start` / `status` / `stop` | Run, inspect, or delete a CAM-vs-control knowledge ablation | `cam_local ab-test status` | Start/stop mutate experiment state; use fixed evaluator and leakage controls |

### Models, benchmark evidence, and promotions

| Command | What it does | Start command | Safety |
| --- | --- | --- | --- |
| `models current` | Show config, corpus, active profile, and role assignments | `cam_local models current` | Read-only |
| `models catalog` | Fetch current provider availability, price, limits, and capabilities | `cam_local models catalog` | Read-only remote |
| `models profile list` / `show` | Inspect available role profiles | `cam_local models profile list` | Read-only |
| `models profile use` | Activate an existing profile | `cam_local models profile use --help` | Configuration mutation; approval required |
| `models benchmark fixtures` | Freeze production-like benchmark fixtures | `cam_local models benchmark fixtures --help` | No model calls |
| `models benchmark plan` | Freeze a worst-case-cost stage | `cam_local models benchmark plan --help` | No model calls; budget contract |
| `models benchmark run` | Execute a frozen stage and store receipts | `cam_local models benchmark run --help` | Provider spend; explicit approval |
| `models benchmark report` | Score completed receipts | `cam_local models benchmark report --help` | Read-only/report write |
| `models benchmark advance` | Freeze the next eligible stage | `cam_local models benchmark advance --help` | No provider calls |
| `models benchmark select` | Recommend quality/budget/speed/batch candidates | `cam_local models benchmark select --help` | No profile change |
| `models set` | Atomically assign a validated model to one role | `cam_local models set --help` | Configuration mutation; approval required |
| `models rollback` | Restore a receipt-backed promotion | `cam_local models rollback --help` | Configuration mutation; approval required |

### Long-running or self-changing operations

| Command | What it does | Start command | Safety |
| --- | --- | --- | --- |
| `pulse status` / `discoveries` / `scans` / `report` / `freshness` | Inspect discovery and stale-repository state | `cam_local pulse status` | Read-only |
| `pulse preflight` | Verify PULSE configuration and key availability | `cam_local pulse preflight` | Read-only; key presence only |
| `pulse scan` / `daemon` | Discover and assimilate GitHub repositories | `cam_local pulse scan --help` | High-risk external discovery and corpus mutation |
| `pulse ingest` / `ingest-hf` / `refresh` | Ingest or refresh selected repositories | `cam_local pulse ingest --help` | Local write / provider spend |
| `self-enhance status` | Report self-enhancement readiness and state | `cam_local self-enhance status` | Read-only indicator, not proof of readiness |
| `self-enhance start` | Clone, enhance, validate, and normally swap a CAM candidate | Use the CAM_Codx packet recipe below | High-risk code mutation |
| `self-enhance validate` | Run the seven validation gates on a candidate | `cam_local self-enhance validate --help` | Candidate validation |
| `self-enhance swap` / `rollback` | Promote or revert a validated candidate | Use the CAM_Codx packet recipe below | Production mutation / rollback only |
| `evolution register` / `status` / `champion-db` | Register and inspect champion state | `cam_local evolution status` | Register mutates state; status is read-only |
| `evolution run` / `loop` | Run one or many budget-bound champion/challenger cycles | `cam_local evolution run --help` | High-risk, provider-backed, long-running |

## 5. CAM MCP tool index

Start a local MCP server for host integration:

```bash
cam_local mcp --transport stdio -c "$CAM_CONFIG"
```

| Tool | Use it for | Default policy |
| --- | --- | --- |
| `claw_query_memory` | Retrieve relevant methods and source evidence | Allow, read-only |
| `claw_verify_claim` | Check a completion claim for placeholders/risk patterns | Allow, read-only |
| `claw_decompose_task` | Turn a request into a CAM-SEQ slot graph | Allow, planning |
| `claw_build_application_packet` | Retrieve component/slot recommendations for a build | Allow, planning |
| `claw_get_run_connectome` | Inspect a reviewed run's connectome | Allow, read-only |
| `claw_trace_failure` | Trace a reviewed run failure backward | Allow, read-only |
| `claw_request_specialist` / `claw_request_specialist_packet` | Choose a bounded specialist handoff | Allow, routing only |
| `claw_list_specialist_exchanges` | Audit durable specialist handoffs | Allow, read-only |
| `claw_store_finding` | Save a verified new pattern | Approval required |
| `claw_escalate` | Record a human-review escalation | Approval required |
| `claw_promote_recipe` | Promote a reviewed run to a compiled recipe | Approval required |
| `claw_queue_mining_mission` | Queue mining from a reviewed run gap | Approval required |
| `claw_export_specialist_exchange` | Write a request envelope to the spool | Approval required |
| `claw_import_specialist_exchange` | Import a schema-checked specialist reply | Approval required; classify recommendations before edits |
| `claw_bridge_specialist_exchange` | Submit/import through an external MCP tool | Approval required; external output is untrusted |
| `claw_submit_specialist_webhook` | Submit through a signed webhook | Approval required; never commit the shared secret |

`route_agent` is the host-pack alias for specialist routing. It recommends an
agent; it does not execute a handoff or authorize an edit.

## 6. CAM_Codx features

### A. Setup wizard and narrow wrapper

The wizard creates a stable `cam-codx` wrapper that pins the runtime, config,
database, and private environment without exposing secrets in commands.

```bash
cd "$CAM_CODEX"
python tools/cam_setup_wizard.py \
  --cam-home ~/CAM \
  --skip-clone \
  --wrapper-cam-cam "$CAM_CAM" \
  --wrapper-db "$CAM_DB" \
  --wrapper-config "$CAM_CONFIG" \
  --wrapper-env "$CAM_CAM/.env" \
  --install-codex-skill \
  --non-interactive

~/CAM/scripts/cam-codx status
```

It installs these four skills under `~/.codex/skills/`:

- `cam-codx-setup` — verify the local CAM installation and narrow wrapper.
- `cam-codx-swe` — build, update, review, and debug a defined SWE task.
- `cam-codx-development-brief` — make an early new-project or rescue decision
  from read-only evidence.
- `cam-codx-pull-mine-dir` — explicitly update eligible repositories, mine one
  pinned `claw.db`, and report whether evidence warrants one `--skip-swap`
  candidate.

### B. Routine SWE skill

Use this in any project where you want CAM evidence without an implicit mining
job:

```text
Use cam-codx-swe to manage this task. Start read-only, recall relevant CAM
methods with provenance, then plan, implement, test, and record outcomes. Do
not mine, spend, promote models, or self-enhance.
```

The skill reads the target's truth files, retrieves methods as suggestions,
requires the target's native tests, and records limitations. It does not turn a
methodology into permission to edit code.

### C. Development Brief: start or rescue a project

Use this before a project plan exists, or when you need an honest decision
about an in-progress repository:

```text
Use cam-codx-development-brief to help me start this new project from relevant prior work.
```

```text
Use cam-codx-development-brief to decide whether this in-progress repository should continue, be mitigated, or be re-developed.
```

The result distinguishes **direct precedent**, **transferable analogy**, and
**new hypothesis**, then states the smallest safe next step. By default it reads
only the named target and explicitly supplied primary corpus. It does not mine,
contact a provider, run target tests, edit code, write `claw.db`, record
retrieval usage, or broaden into sibling corpora. See
[CAM Development Brief](CAM_DEVELOPMENT_BRIEF.md) for the explicit CLI and
later scan-only expansion gate.

### D. Pull, mine, and assess one directory

Use this only when you explicitly want to update and mine a local directory;
routine SWE and the Development Brief do not imply it.

```text
Use cam-codx-pull-mine-dir to update and mine this repository directory. Use --source-root for another user's folder, begin with --dry-run when I ask for preview, pin claw.db and claw.toml, and report the evidence gate.
```

The default source root is
`/Volumes/WS4TB/waswiki/repos2mine/repo622sn`; use
`--source-root /absolute/path/to/repos` elsewhere. A live invocation may update
only clean/upstream repositories via fast-forward Git, write the pinned corpus
and normal ledger, and run at most one supervised `--skip-swap` candidate after
the five-findings/two-repository/repeated-gap gate passes. Dirty, conflicted,
detached, no-upstream, failed-fetch, and non-fast-forward repositories are
reported without stopping later repositories.

`--dry-run` writes a private report but does not fetch, pull, mine, alter
`claw.db`, update the ledger, or issue a candidate packet. `self-enhance swap`,
model/profile changes, rollback, and live configuration changes always need a
separate explicit approval. See [CAM Pull Mine Directory](CAM_PULL_MINE_DIR.md).

### E. Fixed-operation program manager

`tools/cam_manager.py` creates a content-addressed argv packet, a short-lived
single-use approval, and a digest-only receipt. It never executes through a
shell and does not persist `.env` values, prompts, repository contents, or raw
command output.

```bash
STATE=~/CAM/local_state/CAM_Codx/manager

python "$CAM_CODEX/tools/cam_manager.py" prepare models-current \
  --wrapper ~/CAM/scripts/cam-codx --state-dir "$STATE"
python "$CAM_CODEX/tools/cam_manager.py" approve <packet.json> \
  --approved-by operator --state-dir "$STATE"
python "$CAM_CODEX/tools/cam_manager.py" execute <packet.json> \
  --approval <approval.json> --state-dir "$STATE"
```

| Packet phase | Operations |
| --- | --- |
| Inspect | `inspect`, `models-current`, `models-catalog`, `self-enhance-status`, `self-enhance-validate` |
| Benchmark | `benchmark-plan`, `benchmark-run`, `benchmark-report`, `benchmark-advance`, `benchmark-select` |
| Self-enhance | `self-enhance-start` |
| Promote/rollback | `self-enhance-swap`, `self-enhance-rollback`, `models-promote`, `models-rollback`, `models-profile-use` |

The manager does **not** currently allowlist `mine`; do not imply that a normal
SWE packet authorizes corpus mining. Mining remains a separately approved
CAM_CAM operation with explicit root, target, database, config, budget, and
receipt.

### E. Safe self-enhancement recipe

1. Run `self-enhance-status`.
2. Prepare `self-enhance-start` with `--mode supervised`, `--max-tasks 1`, and
   `--skip-swap`.
3. Approve and execute that exact packet once.
4. Inspect protected-file changes, candidate tests, and diff.
5. Only then prepare a distinct `self-enhance-swap` packet with a fresh
   approval. Preserve the backup and rollback receipt.

### F. Agent packs and integrations

CAM_Codx generates host-specific packs from one capability contract:

| Host | Use it for | Verify |
| --- | --- | --- |
| Codex | setup, `cam-codx-swe`, Development Brief, `/goal` contracts | Skill installed; wrapper status works |
| Claude Code | stdio MCP, project `.mcp.json`, CAM skill | `claude mcp list` and pack `smoke.sh` |
| Gemini | stdio MCP plus Gemini skill/config templates | `gemini mcp list` and pack `smoke.sh` |
| Grok Build | stdio MCP, AGENTS/skill/hook templates | `grok inspect` and pack `smoke.sh` |

After changing the capability contract or templates, validate generated packs:

```bash
cd "$CAM_CODEX"
python tools/generate_agent_packs.py --check
python -m pytest -q tests/test_agent_packs.py
git diff --check
```

### G. Evidence-governed build workflows

- **Codex `/goal`**: turn a complex build into a durable completion contract
  with boundaries, acceptance tests, and stop rules.
- **Repo Necromancer**: create a provenance-backed merger/transplant packet
  before combining source repositories; a packet is not a finished product.
- **Agent packs**: give Claude Code, Gemini, and Grok Build the same CAM
  capability and safety contract without forking CAM runtime code.
- **Outcome recording**: retain source method IDs, the actual verification
  command, and the observed result; avoid turning synthetic/smoke evidence into
  a production-quality claim.

## 7. Copy-paste workflows

### Routine update or debugging task

```text
Use cam-codx-swe to manage this SWE task. Inspect repository truth files first,
run CAM read-only recall, propose the smallest coherent change, run repository
tests, and record outcomes. Do not mine, spend, change profiles, or self-enhance.
```

### Start a new project from prior work

```text
Use cam-codx-development-brief to help me start this new project from relevant prior work. Show direct precedents, transferable analogies, mistakes to avoid, and the smallest safe first step. Do not mine, spend, edit code, or scan other repositories.
```

### Continue, mitigate, or re-develop an ongoing repository

```text
Use cam-codx-development-brief to inspect this in-progress repository and recommend continue, mitigate, or re-develop. Read only its truth files, Git state, visible gap markers, and the explicit primary CAM corpus. Do not run tests, mine, write telemetry, or modify the repository.
```

### Mine a bounded set of local repositories

```text
Use cam-codx-session to preflight CAM at /Volumes/WS4TB/waswiki/CAM_CAM and
prepare a scan-only, changed-only mining plan for these exact repos under
/Volumes/WS4TB/waswiki/repos2mine/repo622sn. Pin the moved claw.db and
claw.toml. Do not make model calls, write to the corpus, or generate tasks yet.
```

After inspecting the candidate list, provide a separate explicit authorization
that names: exact repositories, target project, `claw.db`, `claw.toml`, maximum
time, maximum provider spend, `--no-tasks` versus task generation, and the
required evidence report.

### Improve one ongoing repository

```bash
cam_local evaluate /path/to/repo --mode structural -c "$CAM_CONFIG"
cam_local camify /path/to/repo --goal "<outcome>" \
  --output /path/to/repo/CAM_ENHANCEMENT_PLAN.md -c "$CAM_CONFIG"
cam_local enhance /path/to/repo --dry-run --mode supervised --max-tasks 1 \
  -c "$CAM_CONFIG"
```

Approve a real enhancement only after reviewing the plan, dirty state, task
scope, and verification command. Then run the target's own tests and inspect
the diff.

### Build something new using CAM knowledge

1. Use `kb search`, `federate`, or MCP `claw_query_memory` to retrieve methods
   with provenance.
2. Use `ideate` only if the product concept is genuinely open.
3. Create a Codex `/goal` containing outcome, boundaries, acceptance tests,
   privacy/provider rules, and stop conditions.
4. Use `create` only after the output path and write scope are explicit.
5. Validate the generated product with native build/tests and `validate`.

### Prove that CAM added value

1. Freeze one requirement, source snapshot, model policy, budget, and evaluator.
2. Run a control arm without CAM knowledge.
3. Run a CAM arm with the exact same product contract and explicitly logged
   retrieval.
4. Compare acceptance tests, quality rubric, time, cost, tokens, and regression
   risk. Record confounders instead of treating a single demo as proof.

## 8. Completion receipt for any non-trivial run

Record all of the following before calling a run successful:

- exact CAM_CAM, `claw.db`, config, and target paths;
- command and flags; key **names only**, never values;
- repo/fixture list, model IDs, provider budget, and whether tasks were written;
- scan or run receipt, registry/ledger references, and database integrity state;
- target tests/build/security checks and their actual result;
- changed files and diff review;
- source methodology IDs and whether they were accepted, rejected, or need
  investigation;
- residual risks, rollback path, and next recommended action.
