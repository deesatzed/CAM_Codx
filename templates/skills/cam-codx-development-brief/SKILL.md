---
name: cam-codx-development-brief
description: Produce a short, read-only CAM Development Brief for a new project or an in-progress repository. Use when a developer asks what prior work, past mistakes, dissimilar-project analogies, reusable patterns, or next repair should inform starting, continuing, rescuing, mitigating, or re-developing software.
---

# CAM Development Brief

Use this skill only on an explicit request for early-development recall or
continue/rescue advice. Do not run it automatically for ordinary SWE work.

## First pass

1. Read the target's `GOAL.md`, `STANDARDS.md`, `IMPLEMENT.md`,
   `DECISIONS.md`, `PROGRESS.md`, `TASK_QUEUE.md`, and `AGENTS.md` when
   present.
2. Resolve the installed CAM_Codx tool, CAM executable, and primary `claw.db`
   without printing `.env` values or database contents. If they cannot be
   identified, use `cam-codx-setup` first.
3. Choose `new` for a project idea or `continue-rescue` for an in-progress
   repository. The latter requires a named target directory.
4. Run the Development Brief without `--output` first. It prints Markdown and
   reads only the named target plus the supplied primary CAM corpus.

```bash
python /absolute/path/to/CAM_Codx/tools/development_brief.py new \
  --task "Build a durable import retry flow" \
  --target-repo /absolute/path/to/project \
  --cam-command /absolute/path/to/CAM_CAM/.venv/bin/cam \
  --cam-db /absolute/path/to/CAM_CAM/claw.db
```

The first pass must not mine, scan sibling repositories, call a provider,
change a model, write to `claw.db`, execute target tests, create a CAM task, or
modify code. Use `--output /explicit/path/brief.md` only when the developer
asks to save the rendered brief; never write it inside the target repository.

## Interpret the evidence correctly

- **Direct precedent**: compatible stack and task evidence; inspect its source
  before reuse.
- **Transferable analogy**: a dissimilar source with an explicit reason it
  transfers; never treat it as drop-in code.
- **New hypothesis**: an unproven idea; state the validation needed before
  adoption.

Keep confidence and limits attached to every suggestion. Missing test evidence
means `verification not run`, not a pass.

## Choose one next step

End by helping the developer select exactly one: inspect a cited source,
create/update a goal and plan, prepare a bounded mitigation, request a
named-source scan-only expansion, or approve a later implementation phase.

Only offer extra local repositories when the default-scope evidence is thin and
the developer explicitly names the folders. Mining remains a separately
approved CAM phase.
