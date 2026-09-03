# CAM_Codx + Monid Showcase Skills

CAM_Codx can now demonstrate a category of application capability that was
awkward for an independent developer to justify before pay-as-you-go agent
tools: useful external data needed for one launch, one decision, or one product
feature, but not often enough to warrant another standing subscription.

The canonical `cam-codx` skill remains the normal CAM interface. Five optional
skills show how it can identify an external-data gap, inspect candidate Monid
endpoints, expose the price and schema, and test a provider-independent shape.
They are examples of bounded capability acquisition, not five new default CAM
workflows.

## The five outcomes

| Optional skill | What CAM_Codx contributes | What Monid can add | Result |
| --- | --- | --- | --- |
| `cam-codx-monid-capability-spike` | Repository truth, acceptance criteria, adapter design, and tests | Discovery of a missing structured-data capability | Fixture-backed adapter and go/no-go decision |
| `cam-codx-monid-launch-week` | Product context, launch questions, evidence ranking, and follow-ups | Public mentions and community signals for a short launch window | Evidence-linked launch brief |
| `cam-codx-monid-competitive-surface` | The product decision and separation of facts from positioning inference | Public search, brand, company, and news evidence | Competitor and positioning map |
| `cam-codx-monid-product-intelligence` | Normalized application contract and fixture tests | Public price, inventory, product-detail, or review data | Provider-independent product-data adapter proof |
| `cam-codx-monid-incident-context` | Incident truth, timeline discipline, and causation boundaries | Public news, website-health, and outage mentions | External-context timeline that does not replace telemetry |

The useful combination is division of responsibility: CAM_Codx understands the
software work and remembers the evidence boundary; Monid supplies a catalog of
external tools that can be considered only when the application needs them.

## Optional installation

The normal setup remains unchanged and installs only `cam-codx`:

```bash
python tools/cam_setup_wizard.py \
  --cam-home <CAM_HOME> --skip-clone \
  --install-codex-skill --non-interactive
```

Install the five showcases explicitly:

```bash
python tools/cam_setup_wizard.py \
  --cam-home <CAM_HOME> --skip-clone \
  --install-codex-skill --install-monid-showcase-skills \
  --non-interactive
```

That opt-in installs exactly six skills: canonical `cam-codx` and the five
showcases. Existing copies are moved to timestamped recoverable backups with a
`restore.json` map. Unrelated skills are untouched.

## Zero-spend planning

Start with a public subject and a visible ceiling. For a launch-week example:

```bash
python tools/cam_monid_showcase.py \
  --skill cam-codx-monid-launch-week \
  --subject "Example Product public launch" \
  --candidate-limit 5 \
  --max-cost-usd "1.00" \
  --output artifacts/monid-launch-plan.json
```

This helper deliberately has no endpoint-execution feature. It calls only
`monid discover` and `monid inspect`, retains body/query/path schemas, rejects
known outages and candidates beyond the ceiling, and writes a deterministic
artifact containing:

- the discovery queries;
- selected and rejected candidates;
- endpoint health and the published price model;
- projected maximum cost;
- `paid_endpoint_executed: false`.

If an existing dedicated tool already covers the need, pass it with
`--existing-tool <name>`. The planner stops before Monid discovery and records
`dedicated_tool_preferred`. Tool precedence is always:

1. the user's explicit choice;
2. an existing dedicated tool or owned API;
3. Monid for the uncovered capability.

## Paid execution remains a separate decision

Neither installing a skill nor requesting a plan authorizes provider spend.
Before any `monid run`, CAM_Codx must show the inspected endpoint and obtain
explicit authorization for:

- the exact public input;
- endpoint and provider;
- call count and result limit;
- maximum total cost;
- output location.

Any first proof should use one query, one call, and a 5-10 result limit. Save
the output, record actual cost, and stop when the authorized bound is reached.
A `BLOCKED` run is terminal: report the workspace control rather than retrying
or switching providers silently.

No skill may send credentials, local paths, source code, private plans,
customer data, CAM internals, or other confidential material. A result may
support a recommendation; it does not authorize publication, outreach,
purchase, target mutation, production action, or deployment.

## What is tested

Fixture-backed tests prove the planner constructs list-form discovery and
inspection commands, preserves endpoint schemas and decimal prices, rejects
outages and over-budget candidates, prefers existing tools, rejects
secret-shaped subjects, and never invokes a paid endpoint. Setup tests prove
the default and opt-in installation surfaces remain separate and recoverable.

The accompanying
[catalog receipt](reports/2026-09-02-monid-showcase-catalog.md) records the
no-spend discovery evidence used to ground these examples.

The later
[whisky-shopping proof](reports/2026-09-03-monid-whisky-shopping-proof.md)
records two separately bounded paid product searches: 18 results for `$0.151`
total. CAM_Codx rejected mismatched, stale, unavailable, risky, or
destination-unverified leads and preserved both a qualified delivered-price
result and an honest no-match result. No purchase was placed, and a checkout
rate was not relabeled as legal shipping assurance.
