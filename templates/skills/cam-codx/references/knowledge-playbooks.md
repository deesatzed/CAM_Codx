# Knowledge and Mining Playbooks

## Recall existing knowledge

Use `assess` for the safe default Development Brief. Run
`<CAM_CODEX>/tools/development_brief.py` when the developer asks what prior,
adjacent, cloned, unfinished, or dissimilar work can improve a new,
continuing, rescue, or re-development decision. Query only the pinned corpus
and cite provenance; do not require a separate legacy skill entrypoint.

Use `knowledge` for an explicitly named knowledge operation such as searching,
auditing, exporting, comparing, or maintaining existing CAM records. Plan the
exact canonical operation because some apparently read-oriented paths may
initialize local state, use embeddings, access a network, or write an artifact.

## Select reusable evidence

For each finding capture:

- source repository and component;
- method/pattern identifier and evidence state;
- verified successes, failures, fitness, and limitations;
- license/security fit;
- `selected`, `rejected`, or `needs investigation` decision;
- intended adaptation and target check.

Never infer causality from lexical or embedding similarity. Never silently
convert a mined finding into an implementation instruction.

## Explicit mining

Ordinary SWE work never mines. Use the existing coordinator directly only when
the user explicitly requests repository update/mining:

```text
python <CAM_CODEX>/tools/cam_pull_mine_dir.py \
  --source-root <explicit-repository-directory> \
  --cam-command <absolute-cam> --cam-db <absolute-claw.db> \
  --cam-config <absolute-claw.toml> --state-dir <manager-state> --dry-run
```

Pin the source directory, `claw.db`, configuration, model, provider, cost cap,
time bound, and receipt location. Review the dry run before a live invocation.

Mining may update the named corpus and ledger and produce a delta receipt. It
must stop before build selection. Assess the receipt and findings afterward;
create selected/rejected decisions and a landing map as a separate SWE phase.

No implicit mining follows recall. No implicit promotion follows mining.
Promotion is never part of mining. A meaningfulness threshold may authorize
only the separately bounded supervised candidate described by the coordinator;
it never authorizes a model change, source rewrite, live swap, or rollback.
