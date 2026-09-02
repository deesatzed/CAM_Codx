# CAM_Codx Monid Showcase Skills Implementation Plan

> **For Codex:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add five optional, tested CAM_Codx skills that use a shared helper to plan pay-per-use Monid augmentation without changing the canonical default install.

**Architecture:** Five thin skill templates are generated from one machine-readable contract and route zero-spend discovery/inspection through `tools/cam_monid_showcase.py`. The setup wizard installs them only behind an explicit opt-in, while the canonical `cam-codx` skill gains one progressive Monid showcase reference.

**Tech Stack:** Python 3.12+, standard library, PyYAML, pytest, Monid CLI JSON commands, Markdown/YAML/JSON skill assets.

---

### Task 1: Freeze the five-skill contract

**Files:**
- Create: `templates/skills/monid-showcase-contract.json`
- Create: `tests/test_cam_monid_showcase_skills.py`

**Steps:**
1. Write a failing test requiring the five approved names, unique capability
   IDs, concise descriptions, one or two public-safe discovery phrases, and
   safety class `read_only_external_data`.
2. Run `python -m pytest -q tests/test_cam_monid_showcase_skills.py` and confirm
   failure because the contract is missing.
3. Add the minimal JSON contract.
4. Rerun the test and confirm it passes.
5. Commit `feat: define Monid showcase skill contract`.

### Task 2: Build the no-spend Monid planning helper

**Files:**
- Create: `tools/cam_monid_showcase.py`
- Create: `tests/fixtures/monid_showcase/discover.json`
- Create: `tests/fixtures/monid_showcase/inspect.json`
- Create: `tests/test_cam_monid_showcase.py`

**Steps:**
1. Write failing tests for list-form commands, `NO_COLOR=1`, focused discovery,
   inspect-before-selection, body/query/path schema retention, Decimal prices,
   unknown-health eligibility, outage rejection, deterministic redacted JSON,
   existing-tool precedence, and absence of `monid run`.
2. Run the focused test and observe failure.
3. Implement contract loading, an injected command runner, discovery and
   inspection parsing, a bounded selector, and atomic output writing.
4. Add CLI `plan`, `--skill`, `--subject`, `--existing-tool`,
   `--max-cost-usd`, `--candidate-limit`, and `--output` arguments.
5. Rerun focused tests and confirm pass.
6. Commit `feat: add no-spend Monid capability planner`.

### Task 3: Add the five skill templates

**Files:**
- Create: `templates/skills/cam-codx-monid-capability-spike/SKILL.md`
- Create: `templates/skills/cam-codx-monid-capability-spike/agents/openai.yaml`
- Create: `templates/skills/cam-codx-monid-launch-week/SKILL.md`
- Create: `templates/skills/cam-codx-monid-launch-week/agents/openai.yaml`
- Create: `templates/skills/cam-codx-monid-competitive-surface/SKILL.md`
- Create: `templates/skills/cam-codx-monid-competitive-surface/agents/openai.yaml`
- Create: `templates/skills/cam-codx-monid-product-intelligence/SKILL.md`
- Create: `templates/skills/cam-codx-monid-product-intelligence/agents/openai.yaml`
- Create: `templates/skills/cam-codx-monid-incident-context/SKILL.md`
- Create: `templates/skills/cam-codx-monid-incident-context/agents/openai.yaml`
- Modify: `tests/test_cam_monid_showcase_skills.py`

**Steps:**
1. Extend tests to require minimal frontmatter, distinct trigger language,
   matching UI metadata, fewer than 180 body lines, truth-first behavior, the
   shared planner command, all Monid cost/lifecycle gates, and confidentiality
   boundaries.
2. Run and observe missing-template failures.
3. Add the five concise skills and UI metadata.
4. Run the repo validator and Codex quick validator against each directory.
5. Rerun focused tests and confirm pass.
6. Commit `feat: add optional CAM Monid showcase skills`.

### Task 4: Route showcases from canonical CAM_Codx

**Files:**
- Create: `templates/skills/cam-codx/references/monid-showcase-playbooks.md`
- Modify: `templates/skills/cam-codx/SKILL.md`
- Modify: `tests/test_cam_codx_skill.py`

**Steps:**
1. Write a failing test requiring the new progressive reference and explicit
   rule that ordinary CAM work never implies Monid spend.
2. Add one concise route to the canonical skill and keep its body under the
   existing line cap.
3. Add the playbook mapping the five outcomes to optional skills and the
   shared planner.
4. Run `python -m pytest -q tests/test_cam_codx_skill.py`.
5. Commit `feat: route optional Monid showcases from CAM Codex`.

### Task 5: Add explicit optional installation

**Files:**
- Modify: `tools/cam_setup_wizard.py`
- Modify: `tests/test_cam_setup_wizard.py`
- Modify: `templates/skills/cam-codx-setup/SKILL.md`

**Steps:**
1. Write failing tests proving default install remains exactly `cam-codx`, the
   showcase flag requires canonical installation, and opt-in installs exactly
   six named skills with recoverable replacement backups.
2. Add `MONID_SHOWCASE_SKILLS`, extend `install_codex_skills(...,
   include_monid_showcase=False)`, and add CLI flag
   `--install-monid-showcase-skills`.
3. Update setup-skill instructions without changing the default path.
4. Run `python -m pytest -q tests/test_cam_setup_wizard.py`.
5. Commit `feat: install Monid showcase skills on explicit opt in`.

### Task 6: Add public-safe docs and zero-spend receipt

**Files:**
- Create: `docs/CAM_MONID_SHOWCASE_SKILLS.md`
- Create: `docs/reports/2026-09-02-monid-showcase-catalog.md`
- Modify: `README.md`

**Steps:**
1. Document the five user outcomes, optional install command, zero-spend plan
   command, existing-tool precedence, and paid-run approval boundary.
2. Record only the five real catalog searches already performed: timestamp,
   public provider/endpoint, published price model, health, and the explicit
   statement that no paid endpoint ran.
3. Add one README link without presenting five skills as the default CAM UX.
4. Run `git diff --check`.
5. Commit `docs: publish CAM Monid showcase index`.

### Task 7: Verify in a temporary Codex home

**Files:**
- Modify: `tests/test_cam_monid_showcase_skills.py` only if a discovered test
  gap requires it.

**Steps:**
1. Run focused tests for helper, skills, setup, and canonical routing.
2. Run every skill validator.
3. Install canonical plus showcases into a temporary Codex home.
4. Assert exactly six new skill directories and no unrelated mutation.
5. Run the helper against fixtures and verify deterministic receipts.
6. Commit only a genuine test remediation if needed.

### Task 8: Run full release gates and push the feature branch

**Files:**
- No planned new files.

**Steps:**
1. Run `python -m pytest -q`.
2. Run `python tools/generate_agent_packs.py --check`.
3. Run all five skill validators and canonical skill validation.
4. Run `git diff --check` and inspect `git status --short --branch`.
5. Confirm the original canonical checkout retains its pre-existing dirty
   state unchanged.
6. Push `feat/monid-showcase-skills` to origin.
7. Do not merge to `main`, publish externally, or run a paid endpoint without
   a separate approval and review.

