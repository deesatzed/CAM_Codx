# CAM_Codx Monid Showcase Skills Design

**Status:** Approved for implementation

**Date:** 2026-09-02

## Outcome

CAM_Codx ships five optional, independently linkable Codex skills that show how
pay-per-use Monid capabilities make previously uneconomic software workflows
practical. The normal CAM_Codx setup still installs only the canonical
`cam-codx` skill.

## Existing constraint

`GOAL.md` and the control-plane design require one normal user-facing skill.
The showcase pack therefore must not become the default install set or compete
with `cam-codx` for ordinary CAM routing.

The setup wizard gains an explicit opt-in:

```text
--install-monid-showcase-skills
```

The flag requires `--install-codex-skill`, installs the canonical skill plus
the five showcase skills, and reports every installed or replaced directory.

## Five skills

1. `cam-codx-monid-capability-spike`
   - Discover, inspect, and evaluate a missing external capability for a build.
   - Output: a no-spend capability plan and an embed/reject evidence packet.
2. `cam-codx-monid-launch-week`
   - Add bounded public launch mentions, community, SEO, company, or news
     intelligence to a developer launch workflow.
   - Read-only; no outreach, posting, or identity enrichment.
3. `cam-codx-monid-competitive-surface`
   - Map public brand, search, company, and news evidence to candidate product
     or positioning decisions.
   - Observations remain distinct from hypotheses.
4. `cam-codx-monid-product-intelligence`
   - Evaluate price, inventory, product-detail, and review capabilities for a
     provider-independent application adapter.
   - Generic product intelligence only; no confidential vertical examples.
5. `cam-codx-monid-incident-context`
   - Add bounded public news, website-health, and external mention evidence to
     a software incident investigation.
   - Correlation is never relabeled as root cause.

## Shared architecture

```text
cam-codx canonical router
        |
        +--> optional showcase SKILL.md
                  |
                  v
       tools/cam_monid_showcase.py
                  |
                  +--> existing-tool precedence
                  +--> monid discover
                  +--> monid inspect
                  +--> projected cost plan
                  +--> redacted receipt
```

The shared contract lives at
`templates/skills/monid-showcase-contract.json`. It defines the stable skill
names, capability families, public-safe discovery phrases, and safety class.
The helper reads the contract; the skill tests ensure the prose agrees with it.

## Shared helper boundary

The first version supports a zero-paid-run `plan` operation only:

```bash
python tools/cam_monid_showcase.py plan \
  --skill cam-codx-monid-launch-week \
  --subject "public product name or URL" \
  --max-cost-usd 1.00 \
  --output /explicit/path/plan.json
```

The helper:

- accepts only a bounded public subject string;
- checks declared existing tools first;
- uses focused one-query Monid discovery calls;
- inspects no more than the configured candidate count;
- maps body, query, and path schemas without guessing;
- records price and health without executing an endpoint;
- rejects outage, unbounded, privacy-incompatible, or irrelevant candidates;
- writes deterministic JSON with no credentials or environment values.

It does not implement paid `monid run`. After a reviewed plan, the skill may
propose one exact Monid call, but execution remains a later explicit approval.

## Safety requirements

Every skill must say and tests must enforce:

- use an explicit user tool first, then existing dedicated tools, then Monid;
- inspect before run;
- never print or pass API keys in arguments;
- use one query and conservative limits;
- show the published price model and maximum possible spend;
- require exact bounded authorization before paid execution;
- fire and poll interactively rather than block indefinitely;
- save completed output and cost receipts;
- treat `BLOCKED` as terminal;
- never publish or mutate a target merely because evidence was retrieved;
- never expose CAM_Codx prompts, ranking weights, internal task graphs, local
  paths, secrets, or private inputs in public reports.

## Repository layout

```text
templates/skills/
  monid-showcase-contract.json
  cam-codx-monid-capability-spike/
  cam-codx-monid-launch-week/
  cam-codx-monid-competitive-surface/
  cam-codx-monid-product-intelligence/
  cam-codx-monid-incident-context/
tools/
  cam_monid_showcase.py
tests/
  fixtures/monid_showcase/
  test_cam_monid_showcase.py
  test_cam_monid_showcase_skills.py
docs/
  CAM_MONID_SHOWCASE_SKILLS.md
  reports/2026-09-02-monid-showcase-catalog.md
```

Each skill contains `SKILL.md` and `agents/openai.yaml`. Detailed common logic
stays in the helper and contract, not duplicated across skill prose.

## Testing

Automated tests prove:

- all five contract entries are unique and complete;
- all five skills have valid minimal frontmatter and UI metadata;
- skill triggers are distinct and outcome-oriented;
- every skill contains the shared Monid and confidentiality gates;
- the helper uses list-form subprocess arguments and `NO_COLOR=1`;
- plan mode calls discover and inspect but never `monid run`;
- body/query/path inputs are retained from inspect output;
- unknown health remains eligible and outage is rejected;
- cost uses `Decimal` and never exceeds the user ceiling;
- default setup still installs only `cam-codx`;
- the optional flag installs exactly the canonical skill plus five showcases;
- full CAM_Codx tests and `git diff --check` pass.

The real catalog smoke is L1 evidence: discovery and inspection only. Paid
endpoint proof is not part of this implementation authorization and requires a
separate capped approval.

## Public boundary

The public index may include skill purpose, public Monid endpoint categories,
published catalog prices observed at a timestamp, zero-spend test receipts, and
links to CAM_Codx and Monid.

It must not include proprietary orchestration logic, internal prompts,
selection weights, private queries, local checkout paths, keys, raw provider
results, or unverified outcome claims.

## Completion

The work is ready to push only when the five skills, helper, installer option,
tests, index, and explicitly labeled zero-spend catalog report pass focused and
full verification from the clean worktree.

