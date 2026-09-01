# CAM_Codx MONID Evidence Broker Design

**Date:** 2026-09-01  
**Status:** Approved design; initial broker and read-only planning integration implemented; live-proof gate remains opt-in
**Owner:** CAM_Codx  
**External dependency:** MONID CLI/API

## Purpose

Give CAM_Codx a dynamic, bounded way to acquire public structured external
evidence when a task cannot be responsibly decided from local project and CAM
evidence alone. This is an evidence capability, not a replacement for CAM_CAM,
the existing dedicated tools, or Codex judgment.

The normal interaction is:

```text
Outcome-oriented CAM_Codx task
  -> identify a decision-changing external evidence gap
  -> policy-compatible local evidence-cache lookup
  -> MONID discover and inspect on cache miss
  -> bounded MONID run
  -> local raw artifact + reusable receipt + normalized evidence packet
  -> CAM_Codx assessment, recommendation, or explicit unresolved gap
```

CAM_Codx owns the request policy, spend control, provenance receipt, cache
rules, and presentation. MONID supplies external endpoints. CAM_CAM remains
the owner of runtime CLI/MCP behavior, models, mining, retrieval, and its
databases.

## Product Decision

The first slice is a dynamic, one-off evidence broker. It must work across
repository assessment, package/dependency intelligence, product or competitive
research, and other future task types without turning those types into rigid
separate workflows.

CAM_Codx may auto-run a MONID query only when its task policy permits it. The
policy sets a **per-task** budget, allowed source categories, retention class,
prohibited data classes, and task-specific freshness/reuse window. The agent
does not need a per-run confirmation inside that approved policy.

## Evidence Request

Before any external call, CAM_Codx derives a narrow `EvidenceRequest`:

| Field | Meaning |
| --- | --- |
| task ID | The originating CAM_Codx task or SWE Run. |
| evidence question | The exact external fact whose answer could change the decision. |
| decision linkage | The assessment, plan, recommendation, or validation claim it informs. |
| source policy | Allowed providers/categories and excluded providers/categories. |
| budget cap | Maximum spend for all MONID calls attributable to this task. |
| freshness rule | The task-defined interval or condition required for reuse. |
| retention class | Local raw-artifact handling and retrieval visibility. |
| prohibited data classes | Data that must not be requested, retained normally, or exposed. |

CAM_Codx must not issue a MONID request merely because an endpoint is
available. It first determines that an external fact is material to the task's
decision.

## Cache and Reuse

Raw MONID responses are retained locally so a later compatible task can reuse
them without a second paid call. Every artifact is paired with a normalized,
human-inspectable evidence packet and a content hash.

A cache hit is reusable only when all of these hold:

1. its evidence question and parameter fingerprint are compatible with the
   new request;
2. its provider/source policy and retention class are compatible;
3. it is within the new task's declared freshness rule; and
4. it is not quarantined, invalidated, or contradicted in a way that makes it
   unsuitable for the requested decision.

Cached evidence carries its original collection timestamp and cost. Reuse has
zero new MONID cost, but CAM_Codx still records the reuse in the new task's
receipt. Immutable, timestamped evidence may be retained longer than volatile
signals; freshness is decided by the task, not by a global fixed TTL.

## Dynamic Endpoint Routing

On an allowed cache miss, CAM_Codx follows the MONID sequence:

1. run `monid discover` for the narrow evidence question;
2. select the best policy-compatible endpoint, using endpoint health to break
   ties rather than as an exclusion rule;
3. run `monid inspect` and map its real schema before constructing input;
4. reject unknown or over-budget pricing before execution;
5. run the smallest request sufficient to answer the question; and
6. store the raw result and receipt, then normalize only evidence relevant to
   the question.

Existing dedicated user tools, MCP servers, and owned API keys take precedence
over MONID. MONID fills an external-data gap; it is not a silent replacement
for an existing no-extra-cost integration.

## Query-Scoped Catalog Ledger

CAM_Codx does not assume MONID exposes a stable, global catalog. Instead, it
keeps a local snapshot for each evidence question it has actually used. A
refresh records the CLI version, returned provider/endpoint identities,
categories, published price, health, and the inspected-schema digest for the
selected endpoint. The next refresh reports added/removed endpoints, selected
schema changes, and CLI-version changes.

This is an explicit refresh capability, not background monitoring or a paid
evidence run. A material schema drift invalidates cached evidence produced by
that endpoint, preserving the raw artifact and invalidation reason for audit.
New endpoints are reported only within the refreshed question's discovery
scope; CAM_Codx must never describe this as MONID-wide coverage.

## Receipt and Evidence Packet

Each MONID run or cache reuse produces a provenance-bearing receipt containing:

- task ID, evidence question, decision linkage, and policy decision;
- cache hit/miss status and any invalidation reason;
- provider, endpoint, endpoint health, and parameter fingerprint;
- collection/reuse timestamp, actual cost, and cumulative task-budget use;
- raw local artifact reference and content hash;
- normalized claims, source links, and explicit confidence/limitations;
- freshness/reuse deadline or condition; and
- disposition: used, not used, unresolved, failed, quarantined, or rejected.

The evidence packet separates observed source facts from CAM_Codx's inference
and recommendation. A successful endpoint response is evidence, not proof
that a proposed target change is correct or permission to mutate a target.

## Safety and Failure Policy

The broker fails closed before an external call when the task contains
credentials, private repository/content, PHI or sensitive personal data,
legal or clinical conclusions, a forbidden provider/category, unknown price,
or insufficient remaining task budget. These cases become an explicit,
approval-required evidence request.

If no suitable endpoint exists, an endpoint is unavailable, inspection reveals
an incompatible schema, a run fails, or valid sources conflict, CAM_Codx
reports a labeled evidence gap or conflict. It must not fabricate a conclusion
or promote a failed run to validated evidence. Failed attempts retain a
sanitized failure receipt but do not become reusable positive evidence.

Sensitive or policy-violating returned data is quarantined from ordinary CAM
retrieval and requires explicit handling. Raw results, keys, and secrets must
not be printed in conversational output, receipts, or ordinary documentation.

## User Experience

CAM_Codx speaks in evidence and decisions rather than MONID commands. For
example:

> This decision depends on current package-maintenance signals. There is no
> policy-compatible cached evidence. I can query an approved public source
> inside this task's cap and retain the result until the task freshness window
> expires.

After an auto-run it reports source, cost, freshness deadline, cache status,
and whether the evidence changed the recommendation. Users retain direct
controls to request `show evidence`, `reuse only`, `refresh`, or `do not
retain`.

## Proof Gates

Implementation is incomplete until tests demonstrate all of the following:

1. A compatible, fresh cache hit avoids MONID execution and spend.
2. An expired, invalidated, quarantined, or policy-incompatible cache entry
   cannot be reused.
3. Every execution and reuse has a complete, reproducible, redacted receipt.
4. Budget, unknown-price, forbidden-category, and sensitive-data gates stop
   before endpoint execution.
5. Endpoint discovery, inspection, and argument construction use the actual
   inspected schema rather than guessed parameters.
6. A bounded live endpoint test, only after explicit live-spend authorization,
   returns an evidence packet that is useful to its stated decision.
7. CAM_Codx reports observed evidence separately from inference,
   recommendation, and any later implementation outcome.
8. Full relevant CAM_Codx checks and `git diff --check` pass without relabeling
   synthetic or partial proof as live evidence.

## Non-Goals for the First Slice

- recurring monitoring, autonomous feeds, or broad scraping;
- automatic target-repository changes based on external evidence;
- replacing dedicated user-owned service integrations;
- provider/model configuration or CAM_CAM runtime changes; and
- importing sensitive data into ordinary CAM knowledge retrieval.

Those may be considered only after the one-off broker has demonstrated bounded
spend, provenance, cache reuse, and decision usefulness.
