# CAM_Codx Session Skill Implementation Plan

> **For Codex:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a Codex skill that turns semantic CAM_Codx requests into safe CAM/CAM_Codx workflows with preflight, routing, and evidence rules.

**Architecture:** Install a new user-level Codex skill named `cam-codx-session`. Keep executable CAM behavior in CAM_CAM and workflow ownership in CAM_Codx; the skill is a Codex orchestration layer with reference maps and a read-only preflight helper.

**Tech Stack:** Codex skills, Markdown references, Python 3 standard library, local CAM CLI, Git.

---

### Task 1: Initialize Skill Folder

**Files:**
- Create: `/Users/o2satz/.codex/skills/cam-codx-session/SKILL.md`
- Create: `/Users/o2satz/.codex/skills/cam-codx-session/agents/openai.yaml`
- Create directories: `references/`, `scripts/`

**Step 1: Run the skill initializer**

Run:

```bash
python /Users/o2satz/.codex/skills/.system/skill-creator/scripts/init_skill.py cam-codx-session \
  --path /Users/o2satz/.codex/skills \
  --resources scripts,references \
  --interface display_name='CAM_Codx Session' \
  --interface short_description='Semantic CAM workflow manager' \
  --interface default_prompt='Start a CAM_Codx session. Help me choose and run the right CAM workflow with safe preflight, config/database checks, recommendations, and evidence.'
```

Expected: skill directory exists with required files and resource folders.

### Task 2: Write Core Skill Instructions

**Files:**
- Modify: `/Users/o2satz/.codex/skills/cam-codx-session/SKILL.md`

**Step 1: Replace template content**

Include:

- trigger description for "CAM_Codx, ..." semantic requests;
- session workflow;
- intent categories;
- read-only vs mutating action rules;
- config/database/env safety rules;
- report and verification expectations;
- pointers to references and preflight script.

**Step 2: Validate frontmatter**

Run:

```bash
python /Users/o2satz/.codex/skills/.system/skill-creator/scripts/quick_validate.py /Users/o2satz/.codex/skills/cam-codx-session
```

Expected: validation passes.

### Task 3: Add Command Map Reference

**Files:**
- Create: `/Users/o2satz/.codex/skills/cam-codx-session/references/cam-command-map.md`

**Step 1: Map commands to user intents**

Group the CAM command surface into:

- setup and health;
- inspect and decide;
- learn from repos;
- plan and improve;
- create new things;
- validate and prove;
- agent/runtime integration.

**Step 2: Include safety class**

Each command group should indicate whether it is normally read-only, dry-run
first, or mutating.

### Task 4: Add Playbooks Reference

**Files:**
- Create: `/Users/o2satz/.codex/skills/cam-codx-session/references/session-playbooks.md`

**Step 1: Add practical workflows**

Include playbooks for:

- mine then enhance;
- repo enhancement only;
- create from CAM knowledge;
- validate a generated product;
- compare CAM vs non-CAM output;
- setup/new machine diagnostics;
- fleet enhancement;
- self-enhancement/evolution.

**Step 2: Add stop rules**

Document stops for credentials, destructive actions, PHI/sensitive data, high
spend, dirty-tree ambiguity, production deployment, and repeated failures.

### Task 5: Add Preflight Script

**Files:**
- Create: `/Users/o2satz/.codex/skills/cam-codx-session/scripts/cam_session_preflight.py`

**Step 1: Implement read-only checks**

The script should accept:

```bash
--repo /path/to/repo
--cam-cam /path/to/CAM_CAM
--db /path/to/claw.db
--config /path/to/claw.toml
--env-file /path/to/.env
--intent "mine then enhance"
--json
```

It should check:

- path existence;
- git repo and dirty status;
- `cam` CLI presence;
- `OPENROUTER_API_KEY` key name present without printing value;
- config and DB path existence;
- likely SQLite WAL write directory;
- current CAM command names when available.

**Step 2: Test script syntax**

Run:

```bash
python -c "import py_compile; py_compile.compile('/Users/o2satz/.codex/skills/cam-codx-session/scripts/cam_session_preflight.py', cfile='/tmp/cam_session_preflight.pyc', doraise=True)"
```

Expected: no output or success print.

### Task 6: Smoke Test Against TempleOE

**Files:**
- Read-only target: `/Volumes/WS4TB/TempleOE/guardrails-suite`

**Step 1: Run preflight**

Run:

```bash
python /Users/o2satz/.codex/skills/cam-codx-session/scripts/cam_session_preflight.py \
  --repo /Volumes/WS4TB/TempleOE/guardrails-suite \
  --cam-cam /Volumes/WS4TB/repo622sn/CAM_CAM \
  --db /Volumes/WS4TB/repo622sn/CAM_CAM/claw.db \
  --config /Volumes/WS4TB/repo622sn/CAM_CAM/claw.toml \
  --env-file /Volumes/WS4TB/repo622sn/CAM_CAM/.env \
  --intent "mine completed; enhance guardrails-suite"
```

Expected: report prints repo/config/db/env state and does not expose secrets.

### Task 7: Final Validation

**Files:**
- Validate: `/Users/o2satz/.codex/skills/cam-codx-session`

**Step 1: Run skill validator**

Run:

```bash
python /Users/o2satz/.codex/skills/.system/skill-creator/scripts/quick_validate.py /Users/o2satz/.codex/skills/cam-codx-session
```

Expected: `Skill is valid!`

**Step 2: Inspect installed files**

Run:

```bash
find /Users/o2satz/.codex/skills/cam-codx-session -maxdepth 3 -type f -print | sort
```

Expected: `SKILL.md`, `agents/openai.yaml`, both references, and preflight script.
