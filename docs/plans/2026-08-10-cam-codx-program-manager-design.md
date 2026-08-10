# CAM_Codx Program Manager and Phase-Approval Design

**Date:** 2026-08-10  
**Status:** Approved for implementation from the user request  
**Owner:** CAM_Codx  
**Runtime owner:** CAM_CAM

## Outcome

Make CAM_Codx a routine, explicit option for Codex software-engineering work.
The manager must help Codex inspect a target, use CAM knowledge, prepare a
bounded plan, obtain the right approval, execute the selected CAM phase, and
leave a durable evidence trail. It must not silently mine repositories,
change a model profile, write the live corpus, or swap a self-enhanced copy.

## Ownership

CAM_Codx owns the program-management protocol:

- operation allowlists and phase definitions;
- content-addressed execution packets;
- append-only approval and execution receipts;
- the Codex routine skill and operator documentation;
- cross-repo verification and durable progress records.

CAM_CAM remains the owner of executable model, benchmark, mining, and
self-enhancement behavior. The manager invokes CAM only through the generated
`cam-codx` wrapper, which pins the runtime checkout, config, environment, and
database.

## Workflow

The manager exposes these bounded operations:

| Phase | CAM operation | Default safety | Approval |
|---|---|---:|---:|
| `inspect` | status/current model/corpus identity | read-only | no |
| `plan` | benchmark plan or SWE work packet | local artifact only | optional |
| `run` | approved benchmark calls or a bounded SWE action | provider spend or task mutation | required |
| `report` | score/report frozen evidence | read-only corpus access | no |
| `advance` | freeze the next tournament phase | local artifact only | required to continue the tournament |
| `select` | produce role recommendations | read-only | no |
| `self-enhance` | clone, enhance, validate, and optionally stop before swap | source mutation in disposable copy | required |
| `promote` | swap a validated self-enhanced copy or model profile | live mutation | separate required approval |

Every operation is first represented by a JSON execution packet containing an
allowlisted operation, exact argv, resolved wrapper path, target repository,
budget, and a SHA-256 scope digest. `approve` issues an immutable receipt for
that digest. `execute` consumes the receipt once and records the exit status,
stdout/stderr digests, and timestamps. A receipt cannot authorize a changed
packet, a different phase, a different workflow, or a second execution.

## Approval protocol

Approvals are local state, never Git-tracked source:

```text
<CAM_HOME>/local_state/CAM_Codx/manager/
  packets/<packet-id>.json
  approvals/<approval-id>.json
  events.jsonl
```

The state directory is mode `0700`; JSON receipts are mode `0600`. Receipts
contain no environment values, tokens, prompts, repository contents, or raw
command output. Approval scope includes the selected operation, wrapper,
arguments, budget, and relevant path identities. Expired, revoked, consumed,
or mismatched receipts fail closed.

## Routine Codex use

The installed `cam-codx-swe` skill is a workflow option, not a hidden hook. It
instructs Codex to:

1. read the target repository truth files;
2. run CAM read-only inspection and recall when useful;
3. create or update the target's goal/plan before implementation;
4. use the manager for explicit phase transitions and evidence receipts; and
5. reserve mining, provider spend, self-enhancement, profile promotion, and
   live swaps for an explicit user request and matching approval.

This preserves ordinary Codex work when CAM is unavailable and prevents the
mining mistake from becoming the default SWE behavior.

## Self-enhancement boundary

The manager may prepare a supervised self-enhancement packet with a bounded
task count and `--skip-swap`. Validation is a separate evidence gate. A live
swap requires a second `promote` approval, a preserved backup, successful
post-swap validation, and a rollback path. A failed or protected-file result
never becomes a successful enhancement claim.

## Verification

Tests must prove:

1. packet scope digests are deterministic and reject changed argv or paths;
2. read-only operations do not require an approval;
3. mutating/spend operations require the correct unexpired approval;
4. approvals are single-use and execution receipts are append-only;
5. no receipt persists secrets or raw output;
6. the Codex skill explicitly forbids implicit mining and live swaps;
7. CAM_CAM tournament reports account for failed charged calls and preserve
   repeat lineage; and
8. both repositories' focused tests, `git diff --check`, and runtime identity
   checks pass before publication.

