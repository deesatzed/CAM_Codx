# CAM_Codx + Monid Landing Page Implementation Plan

> **For Codex:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a public-safe advertisement-style landing page and an owner-facing email brief that explain Monid's on-demand capabilities through the tested CAM_Codx integration pattern.

**Architecture:** A self-contained static HTML page uses semantic markup, embedded responsive CSS, and minimal progressive-enhancement JavaScript so it works without a web build chain. One focused Python contract test parses both public artifacts and enforces the exact live-versus-fixture evidence boundary, local-link integrity, accessibility basics, and absence of confidential or inflated claims.

**Tech Stack:** HTML5, CSS, vanilla JavaScript, Python standard library `html.parser`, pytest, local `http.server`, browser screenshot tooling.

---

### Task 1: Freeze the public claim and accessibility contract

**Files:**
- Create: `tests/test_cam_monid_landing.py`

**Step 1: Write the failing HTML and brief contract test**

Create a small `HTMLParser` subclass that records titles, headings, section
IDs, links, card markers, and image alt attributes. Require:

```python
LANDING = ROOT / "docs" / "showpieces" / "cam-codx-monid" / "index.html"
BRIEF = ROOT / "docs" / "CAM_CODEX_MONID_OWNER_BRIEF.md"

REQUIRED_SECTIONS = {
    "capability-flow",
    "catalog",
    "showcases",
    "division-of-labor",
    "proof",
    "explore",
}

assert parser.h1_count == 1
assert REQUIRED_SECTIONS <= parser.section_ids
assert parser.showcase_count == 5
assert "prefers-reduced-motion" in html
assert "paid endpoint executed" in normalized_html
assert "none" in proof_boundary
```

Also assert that the landing page and brief contain:

- five live authenticated catalog discoveries;
- fixture-tested discovery/inspection planner behavior;
- no live `monid inspect`, paid `monid run`, polling, or production-app claim;
- links to `../../CAM_MONID_SHOWCASE_SKILLS.md`, the dated catalog receipt,
  and the GitHub feature branch;
- no `/Volumes/`, `monid_live_`, `API_KEY=`, Scotch, Maya, testimonial, partner,
  or endorsement language.

Resolve every relative link against the HTML file and require that it exists.

**Step 2: Run the focused test and verify red evidence**

Run:

```bash
python -m pytest -q tests/test_cam_monid_landing.py
```

Expected: FAIL because the landing page and brief do not exist.

**Step 3: Commit only after Tasks 2 and 3 make the contract green**

Do not commit a permanently red test alone.

### Task 2: Build the standalone advertisement landing page

**Files:**
- Create: `docs/showpieces/cam-codx-monid/index.html`

**Step 1: Implement the semantic page shell**

Add:

- document title under 60 characters;
- meta description under 160 characters;
- skip link, landmark elements, one H1, and the six required section IDs;
- hero headline “Build with the tools you need—only when you need them.”;
- primary in-page CTA to `#showcases` and secondary CTA to `#proof`.

**Step 2: Implement the capability switchboard**

Render six connected nodes:

```text
Product need → CAM_Codx gap decision → Monid discover → inspect schema + price
→ exact authorization → provider-independent adapter
```

Label the authorization/run step “designed, not executed in this proof.” Do not
animate meaning-critical content.

**Step 3: Add five observed catalog cards**

Use only the dated receipt values:

- Strale brand mention search — `$0.3564/call`, stable;
- Ahrefs organic competitors — `$0.042/result`, stable;
- Akta company enrichment — `$0.125/result`, stable;
- Capterra product reviews — `$0.01/call`, stable;
- Context.dev news search — `$0.00009/result`, stable.

State that prices are the `2026-09-02` discovery snapshot and may change.

**Step 4: Add the five application outcome cards**

Each card must use `data-showcase` and contain outcome, CAM_Codx contribution,
Monid capability surface, and evidence artifact for:

1. capability spike;
2. launch week;
3. competitive surface;
4. product intelligence;
5. incident context.

**Step 5: Add division-of-labor and proof ledger sections**

Use three proof columns:

- `EXERCISED LIVE`: CLI version plus five authenticated `monid discover`
  catalog searches;
- `FIXTURE-TESTED`: planner discovery/inspection parsing, cost selection,
  installation, receipts, and skill routing;
- `NOT CLAIMED`: live inspect, paid run, polling, a production application,
  Monid endorsement, or partnership.

**Step 6: Add visual system and progressive enhancement**

Embed CSS variables for graphite, paper, mint, amber, and muted ink. Add
responsive breakpoints at roughly 900px and 620px, visible `:focus-visible`
states, horizontal-overflow protection, and a `prefers-reduced-motion` block.
Use a small intersection observer only to add a reveal class; all content must
remain visible when JavaScript is disabled.

**Step 7: Run the focused test**

Run:

```bash
python -m pytest -q tests/test_cam_monid_landing.py
```

Expected: still FAIL because the brief is missing, while HTML-specific checks
advance beyond the missing-file failure.

### Task 3: Write the Monid owner email and executive-technical brief

**Files:**
- Create: `docs/CAM_CODEX_MONID_OWNER_BRIEF.md`
- Modify: `README.md`

**Step 1: Write two subject lines and ready-to-send email**

Keep the email under 250 words. Lead with the application-building insight,
then say what was built, what real Monid calls were made, what was not run, and
invite review or sharing. Use one primary link to the landing page and a second
source link.

**Step 2: Write the executive-technical brief**

Use these sections:

```markdown
## Executive summary
## The problem we addressed
## What we built
## How the architecture works
## What used a real Monid credential
## Verification and evidence
## Why this matters to Monid
## Boundaries and next proof
## Links
```

Explain that a real authenticated CLI performed five catalog discoveries.
State explicitly that live inspect, paid run, polling, and production app proof
remain unperformed. Describe the five skills, no-spend planner, canonical
routing, opt-in installer, and saved catalog receipt.

**Step 3: Link the landing page from README**

Add one link near the existing optional Monid showcase guide without changing
the canonical default-workflow framing.

**Step 4: Run the focused test and verify green**

Run:

```bash
python -m pytest -q tests/test_cam_monid_landing.py
```

Expected: PASS.

**Step 5: Run whitespace checks and commit**

Run:

```bash
git diff --check
```

Commit:

```bash
git add tests/test_cam_monid_landing.py \
  docs/showpieces/cam-codx-monid/index.html \
  docs/CAM_CODEX_MONID_OWNER_BRIEF.md README.md
git commit -m "docs: add CAM Codex Monid campaign page"
```

### Task 4: Render and visually verify the campaign page

**Files:**
- Modify: `docs/showpieces/cam-codx-monid/index.html` only for observed defects
- Modify: `tests/test_cam_monid_landing.py` only for genuine contract gaps

**Step 1: Start a local server**

Run from the repository root:

```bash
python3 -m http.server 8765
```

Open:

```text
http://127.0.0.1:8765/docs/showpieces/cam-codx-monid/
```

**Step 2: Capture desktop and mobile screenshots**

Capture at approximately `1440×1000` and `390×844`. Inspect the original-size
screenshots for hero hierarchy, card alignment, text measure, overflow,
contrast, proof-boundary prominence, hover/focus behavior, and reduced-motion
fallback.

**Step 3: Correct only observed visual defects**

Use `apply_patch`, recapture both screenshots, and rerun the focused test. If a
change is needed, commit:

```bash
git add docs/showpieces/cam-codx-monid/index.html tests/test_cam_monid_landing.py
git commit -m "fix: polish CAM Codex Monid campaign page"
```

### Task 5: Run release gates and publish the feature branch update

**Files:**
- No planned new files.

**Step 1: Run focused marketing artifact tests**

```bash
python -m pytest -q tests/test_cam_monid_landing.py \
  tests/test_cam_monid_showcase.py tests/test_cam_monid_showcase_skills.py \
  tests/test_cam_setup_wizard.py tests/test_cam_codx_skill.py
```

**Step 2: Run the full suite with the manifest-pinned sibling fixture**

Use a temporary local CAM_CAM clone at the revision pinned by the capability
manifest when the current adjacent runtime is newer. Never modify or reset the
canonical CAM_CAM checkout. Remove only the identity-checked temporary clone
after the run.

Run:

```bash
python -m pytest -q
```

Expected: all tests pass.

**Step 3: Run remaining gates**

```bash
python tools/generate_agent_packs.py --check
git diff --check
git status --short --branch
```

Validate canonical `cam-codx` and all five Monid skill packages with both
frontmatter and Codex quick validators.

**Step 4: Verify repository boundaries**

Confirm:

- feature worktree is clean;
- original canonical CAM_Codx checkout retains its prior dirty state and HEAD;
- no paid Monid endpoint ran;
- no temporary server or sibling clone remains.

**Step 5: Push the existing feature branch**

```bash
git push origin feat/monid-showcase-skills
```

Do not merge, create a PR, deploy, claim Monid endorsement, or publish outside
the existing feature branch without separate authorization.
