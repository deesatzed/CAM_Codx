# CAM_Codx + Monid Landing Page Design

> Historical design boundary: this document records the approved zero-paid-run
> campaign scope on 2026-09-02. Two later bounded paid shopping runs are now
> documented in
> `docs/reports/2026-09-03-monid-whisky-shopping-proof.md`; the public page and
> owner brief were reconciled to that newer evidence without changing the
> self-contained static-page architecture.

## Purpose

Create a public advertisement-style explanation of what Monid makes possible
when CAM_Codx uses it as an on-demand capability layer. The page should make an
independent developer want to explore the pattern and give Monid leadership a
clear, technically credible example they can understand or share.

This is not a partnership announcement, production-app claim, or paid-endpoint
case study. It advertises an implemented and tested integration pattern.

## Audience

The primary audience is Monid ownership and technically strong Monid team
members. The secondary audience is independent developers who understand the
cost of maintaining multiple data subscriptions but may not yet think of a
tool marketplace as an application primitive.

The companion brief must be readable by an executive while retaining enough
architecture and evidence detail for a technical reviewer to audit the claims.

## Positioning

Primary headline:

> Build with the tools you need—only when you need them.

Core message:

> CAM_Codx supplies product context, engineering discipline, and evidence
> gates. Monid supplies discoverable, pay-as-you-go capabilities. Together,
> they let independent developers prototype workflows that previously required
> a shelf of underused subscriptions.

The page presents Monid as a capability-acquisition layer, not merely an API
directory. CAM_Codx is the orchestration and proof layer that turns a product
need into a bounded plan, inspected interface, cost ceiling, normalized
adapter, and testable artifact.

## Page architecture

The landing page is one self-contained, responsive HTML document at
`docs/showpieces/cam-codx-monid/index.html`. It uses semantic HTML, embedded CSS,
and small progressive-enhancement JavaScript. It has no build step, external
font, analytics, unofficial logo, or remote asset dependency.

Sections:

1. **Hero** — outcome-first headline, concise explanation, and links to the
   five showcase builds and proof section.
2. **Capability flow** — product need → CAM_Codx gap decision → Monid discovery
   → schema/price inspection → bounded authorization → application adapter.
   Paid execution is clearly shown as a later, unperformed step.
3. **Capability market** — five real catalog surfaces with the observed
   provider, endpoint, price model, and health from the dated receipt.
4. **Five builds** — capability spike, launch week, competitive surface,
   product intelligence, and incident context. Each card names the software
   outcome rather than advertising a raw command.
5. **Why the combination matters** — what CAM_Codx contributes, what Monid
   contributes, and what the independent developer avoids maintaining.
6. **Proof ledger** — three explicit columns: exercised live, fixture-tested,
   and not claimed. This is the primary trust mechanism.
7. **Closing invitation** — explore the source, guide, and receipt. It invites
   review and sharing without implying endorsement.

## Visual direction

Use a dark graphite surface with warm off-white type, electric mint accents,
and small amber evidence markers. The motif is a capability switchboard:
hairline routes, status dots, terminal-like receipts, and cards that feel like
metered tools becoming available on demand.

The design should feel technical and premium, but not like a generic neon AI
dashboard. Typography is system-native. Motion is limited to a subtle signal
traveling through the capability flow and count-up/reveal behavior; all motion
is disabled for `prefers-reduced-motion`.

## Evidence and claim rules

The page may state:

- five optional CAM_Codx skills were created;
- six skill packages validated, including canonical `cam-codx`;
- five authenticated live `monid discover` searches returned real catalog
  metadata;
- the no-spend planner and installer are fixture-tested;
- the release suite passed at the recorded feature revision;
- no paid endpoint was executed.

The page must state that live `monid inspect`, paid `monid run`, polling, and a
production application were not proven in this work. It must not include token
values, private paths, the Scotch concept, confidential CAM internals, implied
Monid endorsement, or invented testimonials.

Dynamic catalog prices are labeled as a dated snapshot, not a promise.

## Companion email brief

Create `docs/CAM_CODEX_MONID_OWNER_BRIEF.md` with:

1. two subject-line options;
2. a short ready-to-send email;
3. a one-page executive and technical brief;
4. the problem, implementation, architecture, real Monid usage, verification,
   commercial relevance, limitations, and links;
5. a low-pressure invitation for feedback or sharing.

The brief should explain technical terms in plain language without talking down
to the sender. It should equip the sender to answer the predictable question:
“What did you actually run with a real Monid credential?”

## Verification

Add a focused Python test that parses the HTML and verifies:

- one H1 and a useful document title/meta description;
- all required sections and five showcase cards;
- local links resolve;
- the proof ledger contains live, fixture, and not-claimed boundaries;
- no secret-shaped values, private workspace paths, Scotch content, or false
  paid-run language appears;
- the page has responsive and reduced-motion CSS;
- the email brief repeats the exact evidence boundary.

Render the page through a local HTTP server at desktop and mobile widths, take
screenshots, and visually inspect hierarchy, overflow, contrast, and keyboard
focus. Then run focused tests, `git diff --check`, and the full release suite
against its pinned CAM_CAM fixture revision.
