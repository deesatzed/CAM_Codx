# Knowledge and Mining Playbooks

## Recall existing knowledge

Use `assess` for the safe default Development Brief. Invoke
`cam-codx-development-brief` when the developer asks what prior, adjacent,
cloned, unfinished, or dissimilar work can improve a new, continuing, rescue,
or re-development decision. Query only the pinned corpus and cite provenance.

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

Ordinary SWE work never mines. Use the existing `cam-codx-pull-mine-dir`
coordinator only when the user explicitly requests repository update/mining.
Pin the source directory, `claw.db`, configuration, model, provider, cost cap,
time bound, and receipt location. Run its dry run first when required by the
current operator contract.

Mining may update the named corpus and ledger and produce a delta receipt. It
must stop before build selection. Assess the receipt and findings afterward;
create selected/rejected decisions and a landing map as a separate SWE phase.

No implicit mining follows recall. No implicit promotion follows mining.
Promotion is never part of mining. A meaningfulness threshold may authorize
only the separately bounded supervised candidate described by the coordinator;
it never authorizes a model change, source rewrite, live swap, or rollback.
