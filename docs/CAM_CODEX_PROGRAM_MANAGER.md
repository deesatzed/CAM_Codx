# CAM_Codx Program Manager

Use CAM_Codx to state the outcome you need. The canonical `cam-codx` skill
selects every managed CAM_CAM capability from the shared contract; the manager
then binds exact list-form argv, identities, budgets, and one-time approvals.
Direct CAM_CAM use is reserved for runtime troubleshooting, development,
recovery, regression isolation, and expert integration.

CAM_Codx can be the routine workflow manager for Codex software-engineering
tasks without turning every task into a mining job. It owns the plan,
approval, and evidence packet; CAM_CAM owns the runtime action.

## Install the routine skill

From the CAM_Codx checkout:

```bash
python tools/cam_setup_wizard.py \
  --cam-home ~/CAM \
  --skip-clone \
  --install-codex-skill \
  --non-interactive
```

This installs all four Codex skills:

```text
~/.codex/skills/cam-codx/SKILL.md
```

Ask Codex: `Use CAM_Codx to build, update, review, or debug this task.` It
starts with repository truth and CAM read-only recall; it does not mine, spend,
promote a model, or swap CAM automatically.

Use `CAM_Codx` for early decisions too: ask it to assess a new project from
precedents and pitfalls, or to recommend continue, mitigate, or re-develop.
That skill is read-only by default and is deliberately separate from the
manager's approval-governed mutation and spend phases. See
[CAM Development Brief](CAM_DEVELOPMENT_BRIEF.md).

Use `CAM_Codx` only for an explicit directory-wide update and mining request.
The bounded route defaults to
`/Volumes/WS4TB/waswiki/repos2mine/repo622sn` when present; use
`--source-root /absolute/path/to/repos` for another user or machine. Start with
`--dry-run` to inspect eligibility and write a report without Git updates,
mining, `claw.db`/ledger writes, provider use, or a candidate packet.

For a live bounded cycle, the coordinator pins `claw.db` and `claw.toml`,
requires a user-local exact-model/hard-cap file, updates only clean upstream
repositories with fast-forward Git, and emits redacted receipts. The only
automatic CAM-inner action is one manager packet for supervised
`--skip-swap` self-enhancement after the five-findings/two-repository/repeated
pattern-or-gap evidence gate. `self-enhance swap`, model/profile changes,
rollback, and live configuration changes remain separate explicit approvals.
See [CAM Pull Mine Directory](CAM_PULL_MINE_DIR.md).

## Packet and approval flow

Use a local state directory outside Git. The setup overlay's recommended path
is:

```text
~/CAM/local_state/CAM_Codx/manager
```

Prepare a read-only identity check:

```bash
python tools/cam_manager.py prepare models-current \
  --wrapper ~/CAM/scripts/cam-codx \
  --state-dir ~/CAM/local_state/CAM_Codx/manager
```

To assess an already-completed mining-model tournament, ask CAM_Codx to
compare the candidate with the existing mining baseline. It prepares a
read-only packet from the three stage reports; the resulting verdict is
evidence, not a model/profile change:

```bash
python tools/cam_manager.py prepare benchmark-compare \
  --wrapper ~/CAM/scripts/cam-codx \
  --arg=--baseline-model --arg=z-ai/glm-5.2 \
  --arg=--candidate-model --arg=openai/gpt-5.6-luna \
  --arg=--first-round-report --arg=/absolute/first-round.json \
  --arg=--heldout-report --arg=/absolute/heldout.json \
  --arg=--repeat-report --arg=/absolute/repeat.json \
  --state-dir ~/CAM/local_state/CAM_Codx/manager
```

Prepare a bounded self-enhancement attempt only after the user explicitly asks
CAM to improve itself:

```bash
python tools/cam_manager.py prepare self-enhance-start \
  --wrapper ~/CAM/scripts/cam-codx \
  --arg=--mode --arg=supervised \
  --arg=--max-tasks --arg=1 \
  --arg=--skip-swap \
  --budget-usd 0 \
  --state-dir ~/CAM/local_state/CAM_Codx/manager
```

Issue approval for that exact packet:

```bash
python tools/cam_manager.py approve <packet.json> \
  --approved-by operator \
  --state-dir ~/CAM/local_state/CAM_Codx/manager
```

Execute once and retain the receipt:

```bash
python tools/cam_manager.py execute <packet.json> \
  --approval <approval.json> \
  --state-dir ~/CAM/local_state/CAM_Codx/manager
```

After a benchmark `select` report identifies a role candidate, model changes
remain explicit manager phases. Use `models-promote` for `cam models set`,
`models-profile-use` to activate an existing profile, and `models-rollback` to
restore a promotion receipt; each requires a fresh approval for that exact
packet.

The manager records only content digests, paths, status, timestamps, and exit
codes. It never stores `.env` values, API keys, prompts, repository contents,
or raw CAM output. Approval state is mode `0700`; receipt files are `0600`.

## Tournament phases

Model comparison uses the existing CAM_CAM tournament commands. CAM_Codx
should prepare and review each stage separately:

```text
plan → approve run → run → report → approve advance → advance → select
```

The benchmark plan must freeze candidates, fixtures, catalog digests, request
controls, and the budget before provider calls. A report is evidence, not a
profile change. Model promotion and self-enhancement swap are separate
`promote` phases and require new approvals.

## Safety boundary

Normal SWE use should use CAM recall and validation, not `cam mine`. Mining
requires a separate user request, explicit roots/database/config, a frozen
budgeted plan, and an evidence report. Self-enhancement is always staged:
bounded supervised run, validation, protected-file review, then separately
approved swap with backup and rollback.
